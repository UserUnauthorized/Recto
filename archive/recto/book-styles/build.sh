#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p output/pdf previews .qa
typst --version > .qa/compiler-version.txt
for style in reference gbt9704; do
  source=specimen.typ
  if [ "$style" = gbt9704 ]; then source=gbt9704.typ; fi
  typst compile "$source" "output/pdf/$style.pdf" 2>".qa/$style.log"
  rm -f "previews/$style-"*.png
  pdftoppm -r 120 -png "output/pdf/$style.pdf" "previews/$style" >/dev/null 2>&1
  pdfinfo "output/pdf/$style.pdf" >".qa/$style-info.txt"
  pdffonts "output/pdf/$style.pdf" >".qa/$style-fonts.txt"
  pdftotext -layout "output/pdf/$style.pdf" ".qa/$style.txt"
done
