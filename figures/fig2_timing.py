"""Render the timing figure from the included 32-call CSV. Python standard library."""
import argparse
import csv
import html
from pathlib import Path

BG = "#080808"; PANEL = "#141311"; INK = "#ece6dc"; MUTED = "#8c8479"; BODY = "#a39b90"
BRASS = "#f1b84b"; BLUE = "#7f9eff"; CORAL = "#ff7659"
MONO = "'SFMono-Regular', Menlo, Consolas, 'DejaVu Sans Mono', monospace"
SERIF = "Georgia, Gelasio, 'Times New Roman', serif"
SANS = "'Helvetica Neue', Arial, Inter, sans-serif"

def esc(s): return html.escape(s, quote=True)

class Fig:
    def __init__(self, n, eyebrow, headline, subtitle, title, desc, footer, h=800):
        self.h = h; self.parts = []
        self.title, self.desc = title, desc
        self.t(60, 70, f"FIGURE {n} · {eyebrow}", MONO, 20, BRASS, ls=4)
        self.t(58, 128, headline, SERIF, 44, INK)
        self.t(60, 170, subtitle, SERIF, 24, MUTED, italic=True)
        self.parts.append(f'<line x1="60" y1="{h-60}" x2="1140" y2="{h-60}" stroke="{MUTED}" stroke-opacity=".4"/>')
        self.t(60, h-26, footer, SANS, 20, BODY)

    def t(self, x, y, s, fam=SANS, size=20, fill=INK, anchor="start", italic=False, ls=0, op=1, weight=None):
        w = f' font-weight="{weight}"' if weight else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-family="{esc(fam)}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-style="{"italic" if italic else "normal"}" letter-spacing="{ls}" opacity="{op}"{w}>{esc(s)}</text>')

    def raw(self, s): self.parts.append(s)

    def svg(self):
        markers = "".join(
            f'<marker id="m{c[1:]}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="{c}"/></marker>'
            for c in (MUTED, BLUE, CORAL, INK, BRASS))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 {self.h}" width="1200" height="{self.h}" role="img" aria-labelledby="t d">\n'
                f'<title id="t">{esc(self.title)}</title><desc id="d">{esc(self.desc)}</desc><defs>{markers}</defs>\n'
                f'<rect width="1200" height="{self.h}" fill="{BG}"/>\n' + "\n".join(self.parts) + "\n</svg>\n")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()
run = Path(__file__).resolve().parent.parent / "results/2026-10-21-timing/per_call.csv"
with run.open() as data:
    rows = list(csv.DictReader(data))

f=Fig(2,"WHERE THE SECONDS WENT","The first answer paid for loading.",
      "Thirty-two short calls to one 27B model on my MacBook Pro, in the order they ran.",
      "The first answer paid for loading.",
      "A stacked bar chart of 32 calls in run order. Each bar splits into loading, reading the prompt, and writing the answer. "
      "The first bar is about 12.8 seconds, almost all of it loading the model (about 10.2 seconds). Every later bar is between about 2 and 5 seconds, "
      "with loading a sliver of about 0.2 seconds; writing the answer is the largest part, at about 21 tokens per second throughout. "
      "Shorter bars are calls whose answers were shorter.",
      "Oct 21, 2026: Ollama 0.32.14, qwen3.6:27b (Q4_K_M), context 4,096 tokens. Times are Ollama-reported.")
X0,X1,Y0,Y1=110,1140,640,230; ymax=14
def py(v): return Y0-(Y0-Y1)*v/ymax
for t in range(0,15,2):
    y=py(t); f.raw(f'<line x1="{X0}" y1="{y}" x2="{X1}" y2="{y}" stroke="{MUTED}" stroke-opacity="{0.5 if t==0 else 0.18}"/>')
    f.t(X0-14,y+6,str(t),SANS,16,BODY,"end")
f.t(X0-14,Y1-22,"seconds",SANS,16,BODY,"end")
n=len(rows); step=(X1-X0)/n; bw=step*0.68
for i,r in enumerate(rows):
    x=X0+i*step+(step-bw)/2; y=Y0
    for v,c,op in ((float(r['load_s']),CORAL,1),(float(r['prompt_s']),MUTED,0.9),(float(r['output_s']),BRASS,1)):
        h=(Y0-Y1)*v/ymax; y-=h
        f.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{c}" fill-opacity="{op}"/>')
for i in (0,15,31):
    x=X0+i*step+step/2; f.t(x,Y0+26,str(i+1),SANS,15,BODY,"middle")
f.t((X0+X1)/2,Y0+50,"call, in run order",SANS,16,BODY,"middle")
# annotation for first bar
x0=X0+step/2
f.raw(f'<line x1="{x0+bw/2+6}" y1="{py(7)}" x2="{x0+70}" y2="{py(7)}" stroke="{CORAL}" stroke-width="1.5"/>')
f.t(x0+78,py(7)+6,"First call: about 10.2 s of loading, before any answer.",SANS,18,INK)
f.t(x0+78,py(7)+32,"After that, loading took about 0.2 s.",SANS,18,BODY)
# legend
lx,ly=760,250
for j,(lab,c) in enumerate((("Loading the model",CORAL),("Reading the prompt",MUTED),("Writing the answer (about 21 tokens/s)",BRASS))):
    yy=ly+j*28; f.raw(f'<rect x="{lx}" y="{yy-13}" width="16" height="16" fill="{c}"/>'); f.t(lx+26,yy,lab,SANS,17,INK,op=0.92)
args.out.write_text(f.svg(), encoding="utf-8")
