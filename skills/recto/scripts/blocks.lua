-- Preserve semantic section boundaries without feeding layout code to Word.
local function has(el, cls)
  for _, value in ipairs(el.classes) do if value == cls then return true end end
  return false
end

local function typst_text(value)
  return pandoc.write(pandoc.Pandoc({pandoc.Plain({pandoc.Str(value)})}), 'typst')
end

function Math(el)
  if FORMAT == 'typst' then
    local math = pandoc.write(pandoc.Pandoc({pandoc.Plain({el})}), 'typst'):gsub('%s+$', '')
    -- Pandoc 3.9 joins one-letter scripts to adjacent function names.
    -- Restrict the correction to math nodes so literal prose/code never changes.
    for _, name in ipairs({'upright', 'bold', 'italic'}) do
      math = math:gsub('([%^_])([%a])' .. name .. '%(', '%1(%2)' .. name .. '(')
    end
    return pandoc.RawInline('typst', math)
  end
end

function Header(el)
  if FORMAT == 'typst' and os.getenv('RECTO_STYLE') == 'reference' then
    -- The accepted handout gives first-level sections the existing level-2 rule.
    el.level = el.level + 1
  end
  return el
end

function Para(el)
  if FORMAT == 'typst' and os.getenv('RECTO_STYLE') == 'reference' and el.content[1] and el.content[1].t == 'Strong' then
    local rendered = pandoc.write(pandoc.Pandoc({el}), 'typst')
    if #el.content == 1 then
      return pandoc.RawBlock('typst', '#block(above: 1.3em, below: 0.65em, sticky: true)[' .. rendered .. ']')
    end
    return pandoc.RawBlock('typst', '#block(above: 0.85em, below: 0.85em, breakable: true)[' .. rendered .. ']')
  end
end

function Div(el)
  if has(el, 'pagebreak') then
    if FORMAT == 'typst' then return pandoc.RawBlock('typst', '#pagebreak()') end
    return pandoc.Para({pandoc.Str('RECTO_PAGEBREAK')})
  end
  if has(el, 'appendix') then
    local label = el.attributes.label or ''
    local title = el.attributes.title or ''
    if FORMAT == 'typst' then
      local body = pandoc.write(pandoc.Pandoc(el.content), 'typst')
      local head = '#block(height: 2 * line-step, above: 0pt, below: 0pt)[#text(font: hei-font)[' .. typst_text(label) .. ']]\n'
      if label == '' then head = '' end
      body = head .. '#document-title[' .. typst_text(title) .. ']\n' .. body
      if has(el, 'landscape') then
        body = '#context { let n = counter(page).get().first(); let content = [' .. body .. ']; assert(measure(block(width: body-height, content)).height <= body-width, message: "Landscape appendix exceeds one page; split into explicit continuation blocks."); block(width: body-width, height: body-height, breakable: false)[#place(top + left, rotate(if calc.odd(n) { -90deg } else { 90deg }, reflow: true, block(width: body-height, height: body-width, content)))] }'
      end
      return pandoc.RawBlock('typst', '#pagebreak()\n' .. body)
    end
    local out = pandoc.List({pandoc.Para({pandoc.Str(has(el, 'landscape') and 'RECTO_LANDSCAPE' or 'RECTO_PORTRAIT')})})
    if label ~= '' then out:insert(pandoc.Div({pandoc.Para({pandoc.Str(label)})}, pandoc.Attr('', {}, {['custom-style']='Appendix Label'}))) end
    out:insert(pandoc.Div({pandoc.Para({pandoc.Str(title)})}, pandoc.Attr('', {}, {['custom-style']='Appendix Title'})))
    out:extend(el.content)
    out:insert(pandoc.Para({pandoc.Str('RECTO_APPENDIX_END')}))
    return out
  end
end
