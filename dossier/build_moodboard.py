"""Moodboard of the deck: a sober direction, a few decisions, a single accent."""

import base64
import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image  # noqa: E402

from sponsor import scenes  # noqa: E402


def b64(img, w=620):
    img = img.convert("RGB")
    img = img.resize((w, int(img.height * w / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=84)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


photos = [b64(scenes._plate(n)) for n in ("pitch_boards", "minibus", "kit_front")]
swatches = [("Ink", "#1B2430"), ("Navy", "#1F4E8C"), ("Paper", "#FAFAF8"), ("Grey", "#6B7280"), ("Line", "#E5E7EB"), ("Accent", "#F2B705")]
sw = "".join(
    f'<div class="sw"><div class="chip" style="background:{c};{"border:1px solid #E5E7EB" if c == "#FAFAF8" else ""}"></div><b>{n}</b><span>{c}</span></div>'
    for n, c in swatches
)
html = f"""<!doctype html><meta charset="utf-8"><style>
*{{box-sizing:border-box}} body{{margin:0;width:1600px;height:900px;background:#FAFAF8;color:#1B2430;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;padding:56px 64px}}
h1{{font-size:44px;margin:0 0 6px}} .sub{{font-size:20px;color:#6B7280;margin-bottom:34px}}
.grid{{display:grid;grid-template-columns:1.05fr 1fr 1fr;gap:34px}} h3{{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:#1F4E8C;margin:0 0 14px}}
.sws{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .sw{{font-size:15px}} .chip{{height:64px;border-radius:8px;margin-bottom:6px}} .sw span{{display:block;color:#6B7280;font-size:13px}}
.type b{{display:block;font-size:46px;line-height:1.1;margin-bottom:8px}} .type p{{font-size:22px;margin:0 0 8px}} .type small{{font-size:15px;color:#6B7280}}
.photos{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} .photos img{{width:100%;border-radius:8px;display:block}} .photos img:first-child{{grid-column:1/3}}
.rules li{{font-size:19px;margin-bottom:9px}} .rules{{padding-left:20px;margin:0}}
.chart svg{{width:100%}} .bar{{height:14px;border-radius:3px}}
</style>
<h1>Sober sports-tech</h1><div class="sub">Calm, factual, one idea per slide. Real photography, thin lines, one accent used once.</div>
<div class="grid">
<div><h3>Palette</h3><div class="sws">{sw}</div>
<h3 style="margin-top:34px">Type</h3><div class="type"><b>Helvetica Neue</b><p>Titles bold, bullets regular, 28 px minimum on slides.</p><small>Sentence case. No all-caps headlines.</small></div></div>
<div><h3>Photography</h3><div class="photos"><img src="{photos[0]}"><img src="{photos[1]}"><img src="{photos[2]}"></div><p style="font-size:15px;color:#6B7280">Daylight, grass, navy kit. The product shows the sponsor's logo on these scenes.</p></div>
<div><h3>Rules</h3><ul class="rules"><li>Three bullets at most, eight words each</li><li>One visual per slide: photo, bar or line</li><li>Direct labels on charts, no legend box</li><li>Accent yellow marks one thing per slide</li><li>Natural punctuation. No long dashes, no arrows</li><li>Sources in small print, only when needed</li></ul>
<h3 style="margin-top:30px">Chart style</h3><div class="chart"><svg viewBox="0 0 420 110"><line x1="10" y1="90" x2="410" y2="90" stroke="#E5E7EB"/><line x1="10" y1="50" x2="410" y2="50" stroke="#E5E7EB"/><polyline points="10,70 90,84 160,76 240,52 320,30 410,12" fill="none" stroke="#1F4E8C" stroke-width="3" stroke-linecap="round"/><circle cx="410" cy="12" r="5" fill="#1F4E8C"/><text x="10" y="30" font-size="14" fill="#1B2430">One line, one label</text></svg></div></div>
</div>"""
out_html = ROOT / "dossier" / "moodboard.html"
out_png = ROOT / "dossier" / "moodboard.png"
out_html.write_text(html, encoding="utf-8")
chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1600,900", f"--screenshot={out_png}", f"file://{out_html}"], check=True, capture_output=True, timeout=90)
print(out_png)
