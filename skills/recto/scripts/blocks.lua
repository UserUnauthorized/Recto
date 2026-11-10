-- Preserve semantic section boundaries without feeding layout code to Word.
local function has(el, cls)
  return el.classes:includes(cls)
end
local function latex(blocks)
  return pandoc.write(pandoc.Pandoc(blocks), 'latex', {wrap_text='none'})
end
local function text(value)
  return latex({pandoc.Plain({pandoc.Str(value)})}):gsub('[ \t\r\n]+$', '')
end
local function gbt_table(el, landscape)
  -- shortcut: merged cells are rejected; extend only with a cross-format fixture.
  local rows = pandoc.List()
  rows:extend(el.head.rows)
  for _, body in ipairs(el.bodies) do rows:extend(body.head); rows:extend(body.body) end
  rows:extend(el.foot.rows)
  local weights, total = {}, 0
  for i = 1, #el.colspecs do
    local width = 0
    for _, row in ipairs(rows) do
      if #row.cells ~= #el.colspecs then error('Merged table cells are unsupported') end
      local cell = row.cells[i]
      if cell.row_span ~= 1 or cell.col_span ~= 1 then error('Merged table cells are unsupported') end
      local length = 0
      for _, ch in utf8.codes(pandoc.utils.stringify(cell.contents)) do length = length + (ch > 255 and 1 or 0.5) end
      width = math.max(width, length)
    end
    weights[i] = width + 2.2; total = total + weights[i]
  end
  local spec = '|'
  for i, weight in ipairs(weights) do
    local align = ({AlignRight='\\raggedleft', AlignCenter='\\centering'})[tostring(el.colspecs[i][1])] or '\\raggedright'
    spec = spec .. '>{' .. align .. '\\arraybackslash}p{\\dimexpr' .. string.format('%.6f', weight/total) .. '\\linewidth-2\\tabcolsep-2\\arrayrulewidth\\relax}|'
  end
  local environment = landscape and 'tabular' or 'longtable'
  local out = {'\\begingroup\\fontsize{16bp}{24.8bp}\\selectfont\\setlength{\\parindent}{0pt}\\setlength{\\parskip}{0pt}\\renewcommand{\\arraystretch}{1.35}', '\\begin{' .. environment .. '}{' .. spec .. '}\\hline'}
  local header = {}
  for ri, row in ipairs(rows) do
    local cells = {}
    for _, cell in ipairs(row.cells) do
      local rendered = latex(cell.contents):gsub('[ \t\r\n]+$', '')
      cells[#cells+1] = ri <= #el.head.rows and '{\\rectohei ' .. rendered .. '}' or rendered
    end
    local line = table.concat(cells, ' & ') .. ' \\\\\\hline'
    out[#out+1] = line
    if ri <= #el.head.rows then header[#header+1] = line end
    if ri == #el.head.rows and not landscape then
      out[#out+1] = '\\endfirsthead\\hline' .. table.concat(header, '\n') .. '\\endhead'
    end
  end
  out[#out+1] = '\\end{' .. environment .. '}\\par\\endgroup'
  if #el.caption.long > 0 then out[#out+1] = '\\captionof{table}{' .. latex(el.caption.long):gsub('[ \t\r\n]+$', '') .. '}' end
  return pandoc.RawBlock('latex', table.concat(out, '\n'))
end
function Div(el)
  if FORMAT ~= 'docx' then return nil end
  if has(el, 'pagebreak') then return pandoc.Para({pandoc.Str('RECTO_PAGEBREAK')}) end
  if has(el, 'appendix') then
    local label, title = el.attributes.label or '', el.attributes.title or ''
    local out = pandoc.List({pandoc.Para({pandoc.Str(has(el, 'landscape') and 'RECTO_LANDSCAPE' or 'RECTO_PORTRAIT')})})
    if label ~= '' then out:insert(pandoc.Div({pandoc.Para({pandoc.Str(label)})}, pandoc.Attr('', {}, {['custom-style']='Appendix Label'}))) end
    out:insert(pandoc.Div({pandoc.Para({pandoc.Str(title)})}, pandoc.Attr('', {}, {['custom-style']='Appendix Title'})))
    out:extend(el.content)
    out:insert(pandoc.Para({pandoc.Str('RECTO_APPENDIX_END')}))
    return out
  end
end
function Pandoc(doc)
  if FORMAT ~= 'latex' then return nil end
  local course = os.getenv('RECTO_STYLE') == 'reference'
  local function section(el)
    if has(el, 'pagebreak') then return pandoc.RawBlock('latex', '\\clearpage') end
    if has(el, 'appendix') then
      local landscape = has(el, 'landscape')
      local body = pandoc.Pandoc(el.content):walk({Table=function(t) return gbt_table(t, landscape) end, Div=section})
      local label, title = text(el.attributes.label or ''), text(el.attributes.title or '')
      local head = label ~= '' and ('\\rectoappendix{' .. label .. '}{' .. title .. '}') or ('\\rectotitle{' .. title .. '}{}')
      return pandoc.RawBlock('latex', (landscape and '\\begin{rectolandscape}' or '\\clearpage') .. '\n' .. head .. '\n' .. latex(body.blocks) .. (landscape and '\n\\end{rectolandscape}' or ''))
    end
  end
  doc = doc:walk({traverse='topdown', Div=section,
    Table=function(el) if not course then return gbt_table(el, false) end end,
    Para=function(el)
      if course and #el.content == 1 and el.content[1].t == 'Math' and el.content[1].mathtype == 'DisplayMath' then
        return {pandoc.RawBlock('latex', '\\nopagebreak[4]'), el}
      end
      if course and el.content[1] and el.content[1].t == 'Strong' then
        return {pandoc.RawBlock('latex', '\\rectolead'), el}
      end
    end})
  if doc.meta.title then
    local title = latex({pandoc.Plain(doc.meta.title)}):gsub('[ \t\r\n]+$', '')
    local subtitle = doc.meta.subtitle and latex({pandoc.Plain(doc.meta.subtitle)}):gsub('[ \t\r\n]+$', '') or ''
    doc.blocks:insert(1, pandoc.RawBlock('latex', '\\rectotitle{' .. title .. '}{' .. subtitle .. '}'))
  end
  doc.meta = {}
  return doc
end
