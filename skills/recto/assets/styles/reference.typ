// Shared visual grammar measured from the two user-supplied course handouts.
// Songti SC and Times New Roman are local fonts; do not redistribute them.
#let reference-layout(body) = {
  set page(
    width: 595pt, height: 842pt,
    margin: (x: 27.75pt, y: 12mm),
    header: none,
    footer-descent: 4mm,
    footer: context align(center)[
      #text(font: "Times New Roman", size: 10pt, fill: black)[#counter(page).display("1")]
    ],
  )
  set text(
    font: ((name: "Times New Roman", covers: "latin-in-cjk"), "Songti SC"),
    size: 12pt, fill: black, lang: "zh", region: "CN",
    top-edge: 0.8em, bottom-edge: -0.2em,
    cjk-latin-spacing: auto,
  )
  set par(justify: false, first-line-indent: 0pt, leading: 0.5em, spacing: 9pt)
  show math.equation: set text(font: ("New Computer Modern Math", "Songti SC"), size: 1.21em)
  show math.equation.where(block: true): set block(above: 14pt, below: 14pt)
  show heading.where(level: 2): it => block(above: 20pt, below: 10pt, sticky: true)[
    #line(length: 100%, stroke: 0.5pt)
    #v(12pt)
    #text(size: 13.5pt, weight: "bold")[#counter(heading).display()#h(0.6em)#it.body]
  ]
  show figure.caption: set text(size: 10.5pt)
  show table: set text(size: 10.5pt)
  show footnote.entry: set text(size: 9pt)
  body
}

#let reference-title(title, subtitle) = block(below: 16pt)[
  #v(12pt)
  #text(size: 16.5pt, weight: "bold")[#title]
  #v(7pt)
  #text(size: 13.5pt, weight: "bold")[#subtitle]
  #v(10pt)
  #line(length: 100%, stroke: 0.5pt)
]
