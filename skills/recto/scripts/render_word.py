#!/usr/bin/env python3
"""Run the document skill renderer with explicit local font access on macOS."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from xml.sax.saxutils import escape

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('docx',type=Path)
p.add_argument('--renderer',type=Path,required=True,help='documents skill render_docx.py')
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy()
if sys.platform=='darwin':
    # The renderer changes its child HOME to a temporary directory. Use absolute
    # font roots so its bundled LibreOffice still sees installed CJK fonts.
    dirs=[Path('/System/Library/Fonts'),Path('/System/Library/Fonts/Supplemental'),Path('/Library/Fonts'),Path.home()/'Library/Fonts',Path(__file__).resolve().parents[1]/'assets/fonts']
    conf=out/'fonts.conf'
    conf.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig>'+''.join('<dir>'+escape(str(x))+'</dir>' for x in dirs if x.is_dir())+'<cachedir>'+escape(str(out/'font-cache'))+'</cachedir></fontconfig>')
    env['FONTCONFIG_FILE']=str(conf)
subprocess.run([sys.executable,str(a.renderer.resolve()),str(a.docx.resolve()),'--output_dir',str(out),'--emit_pdf'],env=env,check=True)
