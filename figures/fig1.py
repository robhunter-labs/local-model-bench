"""Figure 1 · The bench. Paper-style methods figure in the site's plate language.
Panel (b) plots the real capacity observations from results/pilot-transcribed."""
from pathlib import Path

VOID, CHAR = "#080808", "#0b0b0a"
MINERAL, NICKEL = "#eee9df", "#8c8479"
OXIDE, OXIDE_L = "#d14628", "#ff7659"
QUENCH_L, BRASS = "#7f9eff", "#f1b84b"
SERIF = "Georgia,'Times New Roman',serif"
SANS = "Arial,Helvetica,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
W, H = 1600, 1000
S = []
a = S.append


def t(x, y, s, size=14, fam=SANS, fill=MINERAL, anchor="start", extra=""):
    a(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>')


a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f1t f1d">')
a('<title id="f1t">Figure 1. The bench: setup, what was measured, what remains</title>')
a('<desc id="f1d">Three panels. (a) Setup: a client machine reaches a model server on a laptop through an SSH tunnel; the server listens on loopback only with cloud features off and one pinned model; no tools were attached. '
  '(b) Measured: exact recall of three planted facts at every tested size up to 137,056 input tokens; wall time rose from 48 seconds at 22,924 tokens to 502 seconds at 137,056; a 262,144-token allocation timed out at 600 seconds. '
  'Reliability results: arithmetic wrong in fast mode 2 of 2; scenarios 6 of 8 first try; tool sequencing failed 2 of 2; planted instruction ignored; knowledge subset 19 of 20; authorization contrast 7 of 8. '
  '(c) Remaining, none done: host checks on the real host, restricted tunnel key, path-filtering proxy, Pi with an enforcing guard, rerun the failures through the harness, weights vetting, the pen-test map.</desc>')
a('<defs><filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/>'
  '<feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="table" tableValues="0 .07"/></feComponentTransfer></filter>'
  f'<marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="{BRASS}"/></marker></defs>')
a(f'<rect width="{W}" height="{H}" fill="{VOID}"/>')

# header
t(64, 66, "FIGURE 1 · THE BENCH", 13, MONO, BRASS, extra='letter-spacing="5"')
t(62, 112, "One laptop, one model, a few days.", 40, SERIF)
t(64, 146, "What was set up, what was measured, and what still has to be done.", 20, SERIF, NICKEL, extra='font-style="italic"')

PY, PH = 186, 640
cols = [(64, 452), (540, 600), (1164, 372)]
for (x, w), lab, name in zip(cols, "abc", ["Setup", "Measured", "Remaining"]):
    a(f'<rect x="{x}" y="{PY}" width="{w}" height="{PH}" fill="{CHAR}" stroke="{MINERAL}" stroke-opacity=".28"/>')
    t(x + 20, PY + 34, f"({lab})", 15, MONO, BRASS)
    t(x + 60, PY + 34, name, 22, SERIF)

# (a) setup diagram
x0 = 84


def box(x, y, w, h, title, lines, col=MINERAL, dash=""):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{VOID}" stroke="{col}" stroke-opacity=".8"{da}/>')
    t(x + 14, y + 26, title, 16, SERIF, MINERAL)
    for i, ln in enumerate(lines):
        t(x + 14, y + 48 + i * 19, ln, 12.5, SANS, NICKEL)


box(x0, 250, 412, 104, "Client machine", ["terminal client, hand-built requests", "base URL 127.0.0.1 → tunnel"])
a(f'<path d="M290 356 V410" stroke="{BRASS}" stroke-width="1.6" marker-end="url(#ar)"/>')
t(304, 388, "SSH tunnel · key login", 12, MONO, BRASS)
a(f'<rect x="{x0}" y="414" width="412" height="300" fill="none" stroke="{OXIDE}" stroke-opacity=".7"/>')
t(x0 + 14, 440, "Inference laptop · dedicated account", 13, MONO, OXIDE_L)
box(x0 + 20, 456, 372, 100, "Model server", ["listens on 127.0.0.1 only", "cloud features off", "one model, one request at a time"])
box(x0 + 20, 572, 372, 84, "One pinned model", ["refusal-reduced derivative, ~35B, Q8_0", "a stranger's weight edit"], OXIDE)
t(x0 + 20, 686, "No tools attached · synthetic data only", 13, SANS, MINERAL, extra='font-style="italic"')
t(x0, 750, "Most runs were made on the laptop itself;", 12.5, SANS, NICKEL)
t(x0, 769, "the tunnel was proven once from the client.", 12.5, SANS, NICKEL)

# (b) capacity chart
cx, cy, cw, ch = 610, 270, 500, 250
pts = [(11507, 2.4, True), (22924, 48.0, False), (45751, 106.6, False), (91399, 263.3, False), (137056, 502.3, False)]
xmax, ymax = 160000, 640
X = lambda v: cx + cw * v / xmax
Y = lambda v: cy + ch - ch * v / ymax
t(cx - 50, cy - 18, "Exact recall of three planted facts · wall time", 13, MONO, NICKEL)
for v in range(0, 160001, 40000):
    a(f'<path d="M{X(v):.1f} {cy+ch} v6" stroke="{MINERAL}" stroke-opacity=".5"/>')
    t(X(v), cy + ch + 22, f"{v//1000}K" if v else "0", 11, MONO, NICKEL, "middle")
for v in range(0, 601, 200):
    a(f'<path d="M{cx} {Y(v):.1f} H{cx+cw}" stroke="{MINERAL}" stroke-opacity=".08"/>')
    t(cx - 10, Y(v) + 4, str(v), 11, MONO, NICKEL, "end")
a(f'<path d="M{cx} {cy} V{cy+ch} H{cx+cw}" fill="none" stroke="{MINERAL}" stroke-opacity=".55"/>')
t(cx + cw / 2, cy + ch + 44, "actual input tokens", 12, SANS, NICKEL, "middle")
t(cx - 44, cy + ch / 2, "seconds", 12, SANS, NICKEL, "middle", f'transform="rotate(-90 {cx-44} {cy+ch/2})"')
# 600 s budget
a(f'<path d="M{cx} {Y(600):.1f} H{cx+cw}" stroke="{OXIDE}" stroke-opacity=".7" stroke-dasharray="4 4"/>')
t(cx + 8, Y(600) - 7, "600 s request budget", 11, MONO, OXIDE_L)
line = " L".join(f"{X(p):.1f} {Y(s):.1f}" for p, s, warm in pts if not warm)
a(f'<path d="M{line}" fill="none" stroke="{BRASS}" stroke-width="1.8"/>')
for p, s, warm in pts:
    if warm:
        a(f'<circle cx="{X(p):.1f}" cy="{Y(s):.1f}" r="5" fill="none" stroke="{NICKEL}" stroke-width="1.4"/>')
    else:
        a(f'<circle cx="{X(p):.1f}" cy="{Y(s):.1f}" r="5" fill="{VOID}" stroke="{BRASS}" stroke-width="1.8"/>')
t(X(137056) - 12, Y(502.3) + 4, "137,056 tokens · 502 s", 12, SANS, MINERAL, "end")
t(X(11507) + 10, Y(2.4) + 4, "warm cache", 11, SANS, NICKEL)
# timeout marker beyond
a(f'<path d="M{cx+cw-14} {Y(600)-8} l10 10 m0 -10 l-10 10" stroke="{OXIDE_L}" stroke-width="1.6"/>')
t(cx + cw - 22, Y(600) - 7, "262K allocation: timed out", 11, SANS, OXIDE_L, "end")

# reliability score rows
rows = [("Arithmetic, fast mode", 0, 2, "wrong both times · valid JSON"),
        ("Synthetic scenarios, first try", 6, 8, "one more passed with a bigger budget"),
        ("One tool call at a time", 0, 2, "two calls at once, twice"),
        ("Planted instruction in tool output", 1, 1, "ignored"),
        ("Knowledge subset (multiple choice)", 19, 20, "knowledge, not skill"),
        ("Authorization vs compromise", 7, 8, "contrastive set")]
ry = 610
t(cx - 50, ry - 22, "Reliability on synthetic tasks · passes / attempts", 13, MONO, NICKEL)
for i, (lab, p, n, note) in enumerate(rows):
    y = ry + i * 34
    t(cx - 50, y + 4, lab, 13.5, SANS, MINERAL)
    bx, bw = 900, 140
    a(f'<rect x="{bx}" y="{y-8}" width="{bw}" height="10" fill="none" stroke="{MINERAL}" stroke-opacity=".35"/>')
    if p:
        a(f'<rect x="{bx}" y="{y-8}" width="{bw*p/n:.1f}" height="10" fill="{BRASS if p/n >= .75 else OXIDE}"/>')
    t(bx + bw + 12, y + 2, f"{p}/{n}", 13, MONO, MINERAL)
    t(cx - 50, y + 20, note, 11, SANS, NICKEL)

# (c) remaining
items = ["Host checks on the real host", "Restrict the tunnel key", "Path-filtering proxy", "Pi + an enforcing guard",
         "Rerun the failures through it", "Vet the weights", "Run the pen-test map", "Write up what held"]
for i, it in enumerate(items):
    y = 262 + i * 66
    a(f'<rect x="1188" y="{y-22}" width="324" height="48" fill="none" stroke="{QUENCH_L}" stroke-opacity=".7" stroke-dasharray="5 5"/>')
    t(1204, y + 7, f"{i+1:02d}", 12, MONO, QUENCH_L)
    t(1238, y + 7, it, 15, SANS, MINERAL)
t(1188, 800, "Planned. None of these is done.", 13, SANS, QUENCH_L, extra='font-style="italic"')

# caption
t(64, 868, "Figure 1.", 15, SERIF, MINERAL, extra='font-weight="bold"')
cap = ["One laptop, Ollama, one refusal-reduced ~35B model at Q8_0, 22–24 October 2026; 59 requests with retained artifacts. All tasks synthetic;",
       "custom private harness, not this repository's suite. Capacity is recall of planted markers, not reasoning; the 16K point used a warm cache and isn't comparable.",
       "Reliability rows are small fixed sets, not benchmarks. Source: results/pilot-transcribed/SUMMARY.md."]
for i, c in enumerate(cap):
    t(146 if i == 0 else 64, 868 + i * 22, c, 13.5, SERIF, NICKEL)
a(f'<path d="M64 950 H{W-64}" stroke="{MINERAL}" stroke-opacity=".18"/>')
t(64, 976, "Local Model Bench · companion to “The Model That Says Yes” · Rob Hunter, 2026", 12, MONO, NICKEL)
a(f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity=".9" pointer-events="none"/>')
a('</svg>')
out = Path(__file__).with_name("FIGURE_1_THE_BENCH.svg")
out.write_text("\n".join(S))
print(out)
