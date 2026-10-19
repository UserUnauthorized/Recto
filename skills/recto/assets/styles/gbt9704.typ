// GB/T 9704-2012 body/table/attachment subset, without letterhead or signatures.
#let body-font = recto-fonts.body
#let title-font = recto-fonts.title
#let hei-font = recto-fonts.hei
#let kai-font = recto-fonts.kai
#let body-size = 16pt
#let body-width = 156mm
#let body-height = 225mm
#let glyph-gap = (body-width - 28 * body-size) / 27
#let char-step = body-size + glyph-gap
#let line-gap = (body-height - 22 * body-size) / 21
#let line-step = body-size + line-gap

// Vector rules anchor their upper edges exactly 7mm below the body frame.
#let page-folio() = context {
  let n = counter(page).get().first()
  let number = text(font: recto-fonts.folio, size: 14pt, tracking: 0pt, top-edge: 0.8em, bottom-edge: -0.2em)[#n]
  let number-width = measure(number).width
  let rule-width = 14pt
  let gap = 3.5pt
  let total = 2 * rule-width + 2 * gap + number-width
  let x = if calc.odd(n) { 28mm + body-width - 14pt - total } else { 28mm + 14pt }
  let y = 37mm + body-height + 7mm
  place(top + left, dx: x, dy: y)[
    #rect(width: rule-width, height: 0.5pt, fill: black, stroke: none)
  ]
  place(top + left, dx: x + rule-width + gap, dy: y - 7pt)[#number]
  place(top + left, dx: x + rule-width + 2 * gap + number-width, dy: y)[
    #rect(width: rule-width, height: 0.5pt, fill: black, stroke: none)
  ]
}

#let gbt-layout(body) = {
  set page(paper: "a4", margin: (top: 37mm, bottom: 35mm, left: 28mm, right: 26mm),
    header: none, footer: none, foreground: page-folio())
  set text(font: body-font, size: body-size, weight: "regular", fill: black,
    lang: "zh", region: "CN", tracking: glyph-gap, top-edge: 0.8em, bottom-edge: -0.2em,
    cjk-latin-spacing: none, overhang: false)
  set par(justify: true, leading: line-gap, spacing: line-gap,
    first-line-indent: (amount: 2 * char-step, all: true))
  set heading(numbering: none)
  show math.equation: set text(font: (recto-fonts.math, body-font))
  show heading: it => block(width: 100%, above: line-gap, below: line-gap, sticky: true)[
    #set text(font: if it.level == 1 { hei-font } else if it.level == 2 { kai-font } else { body-font },
      size: body-size, weight: "regular")
    #set par(first-line-indent: 0pt)
    #h(2 * char-step)#it.body
  ]
  body
}

#let document-title(body) = block(width: 100%, above: 0pt, below: line-step, sticky: true)[
  #set par(first-line-indent: 0pt, justify: false, leading: 14pt)
  #align(center, text(font: title-font, size: 22pt, tracking: 0pt,
    weight: if title-font == "FandolSong" { "bold" } else { "regular" })[#body])
]

#let attachment-list(titles) = block(above: line-step + line-gap, below: 0pt)[
  #set par(first-line-indent: 0pt, justify: false)
  #pad(left: 2 * char-step)[
    #grid(columns: (3 * char-step, auto, 1fr), column-gutter: 0pt, row-gutter: line-gap,
      ..titles.enumerate().map(((i, title)) => (
        if i == 0 { [附件：] } else { [] }, [#(i + 1).#h(0.25em)], title,
      )).flatten())
  ]
]

// Keep the supplied label if source material calls it 附录 rather than 附件.
#let attachment-heading(number, title, label: "附件") = {
  block(height: 2 * line-step, above: 0pt, below: 0pt)[
    #set par(first-line-indent: 0pt, justify: false)
    #text(font: hei-font, size: body-size, weight: "regular")[#label#number]
  ]
  document-title(title)
}

#let attachment(number, title, body, label: "附件") = {
  pagebreak()
  attachment-heading(number, title, label: label)
  body
}

#let grid-table(columns, header, rows, cell-size: 16pt) = block(above: line-gap, below: line-gap)[
  #set text(size: cell-size, tracking: 0pt)
  #set par(first-line-indent: 0pt, justify: false, leading: 0.55em, spacing: 0pt)
  #table(columns: columns, align: left + horizon, inset: (x: 6pt, y: 7pt), stroke: 0.5pt,
    table.header(..header.map(x => text(font: hei-font, weight: "regular")[#x])),
    ..rows.flatten())
]

// Landscape table content rotates within a portrait A4 sheet. Folios stay upright.
#let landscape-attachment(number, title, body, continuation: false) = {
  pagebreak()
  context {
    let n = counter(page).get().first()
    block(width: body-width, height: body-height, above: 0pt, below: 0pt, breakable: false)[
      #place(top + left, rotate(if calc.odd(n) { -90deg } else { 90deg }, reflow: true,
        block(width: body-height, height: body-width, above: 0pt, below: 0pt)[
          #if continuation {
            document-title([#title（续）])
          } else {
            attachment-heading(number, title)
          }
          #body
        ]))
    ]
  }
}
