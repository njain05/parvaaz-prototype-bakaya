"""Make the artifact copy of mockup/index.html: CSS inlined, no document skeleton (the publisher adds one)."""
import re, sys
src, css, out = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
s = s.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + open(css, encoding="utf-8").read() + "</style>")
s = re.sub(r"<!doctype html>\s*|</?html[^>]*>\s*|</?head>\s*|</?body>\s*", "", s)
s = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>\s*', "", s)
open(out, "w", encoding="utf-8").write(s)
