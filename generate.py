#!/usr/bin/env python3
"""
Eigenlicht — ein Selbstporträt, das sich aus dem eigenen Commit-Verlauf zeichnet.

Jedes Tagesbild wird deterministisch aus
    sha256("<datum>|<sha des letzten Kunst-Commits>")
erzeugt. Damit hängt jedes Bild an seinem Vorgänger: eine Kette, die mit dem
Repo wächst. Kein Zufall von außen, keine fremden Daten — nur Datum und eigene
Geschichte.

Aufruf:
    python generate.py                                   # heutiges Bild
    python generate.py --force                           # neu zeichnen
    python generate.py --date 2026-11-05 --seed ab12...  # Vorschau/Test
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import math
import pathlib
import random
import subprocess
import sys
from math import cos, radians, sin

ROOT = pathlib.Path(__file__).resolve().parent
ART = ROOT / "art"
W = 1000
CX = CY = W / 2

# ---------------------------------------------------------------- Werkzeuge


def git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return ""


def seed_for(date: str, prev_sha: str) -> str:
    return hashlib.sha256(f"{date}|{prev_sha}".encode()).hexdigest()


def hsl(h: float, s: float, l: float, a: float = 1.0) -> str:
    if a >= 1:
        return f"hsl({h % 360:.1f} {max(0,min(100,s)):.0f}% {max(0,min(100,l)):.1f}%)"
    return f"hsl({h % 360:.1f} {max(0,min(100,s)):.0f}% {max(0,min(100,l)):.1f}% / {a:.3f})"


def f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def pt(ang_deg: float, radius: float, cx: float = CX, cy: float = CY) -> tuple[float, float]:
    a = radians(ang_deg - 90)
    return cx + radius * cos(a), cy + radius * sin(a)


# ---------------------------------------------------------------- Zeichnung


def draw(seed: str, date: str) -> str:
    r = random.Random(int(seed, 16))
    h0 = r.uniform(0, 360)
    h1 = h0 + r.choice([32, 46, 150, 168, 196, -38])
    h2 = h0 + r.choice([-96, -72, 84, 104, 132, 158])
    n = r.choice([8, 9, 10, 11, 12, 13, 14])
    step = 360 / n
    sat = r.uniform(58, 84)
    tilt = r.uniform(0, step)
    style = r.choice(["astrolabium", "bloom", "lattice"])

    ink = hsl(h0, sat * 0.9, 92)
    defs: list[str] = []
    el: list[str] = []

    # --- Grund
    defs.append(
        '<radialGradient id="bg" cx="50%" cy="47%" r="72%">'
        f'<stop offset="0%" stop-color="{hsl(h0, 38, 13)}"/>'
        f'<stop offset="48%" stop-color="{hsl(h0, 30, 7)}"/>'
        '<stop offset="100%" stop-color="#030407"/></radialGradient>'
    )
    defs.append(
        '<radialGradient id="bloom" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{hsl(h1, 80, 62, 0.5)}"/>'
        f'<stop offset="55%" stop-color="{hsl(h1, 80, 50, 0.10)}"/>'
        f'<stop offset="100%" stop-color="{hsl(h1, 80, 50, 0)}"/></radialGradient>'
    )
    defs.append(
        '<filter id="soft" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="14"/></filter>'
    )
    defs.append(
        '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.85" '
        'numOctaves="4" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>'
    )
    for i, (r0, l) in enumerate(((0.10, 34), (0.62, 74))):
        defs.append(
            f'<radialGradient id="petal{i}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="{f(r0*100)}%" stop-color="{hsl(h1, sat*0.7, l, 0.03)}"/>'
            f'<stop offset="72%" stop-color="{hsl(h1, sat, l, 0.10)}"/>'
            f'<stop offset="97%" stop-color="{hsl(h0, sat, l+6, 0.22)}"/>'
            f'<stop offset="100%" stop-color="{hsl(h0, sat, l+6, 0)}"/></radialGradient>'
        )

    el.append(f'<rect width="{W}" height="{W}" fill="url(#bg)"/>')
    # weicher Lichtkern, leicht aus der Mitte gerückt
    off = r.uniform(0, 360)
    gx, gy = pt(off, r.uniform(0, 40))
    el.append(
        f'<circle cx="{f(gx)}" cy="{f(gy)}" r="{f(r.uniform(220,300))}" '
        f'fill="url(#bloom)" filter="url(#soft)"/>'
    )

    # --- Sternenstaub
    dots = []
    for _ in range(r.randint(110, 190)):
        a = r.uniform(0, 360)
        rad = 470 * (r.random() ** 0.55)
        x, y = pt(a, rad)
        dots.append(
            f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r.uniform(0.35,1.5))}" '
            f'fill="{ink}" opacity="{f(r.uniform(0.05,0.45))}"/>'
        )
    el.append(f'<g>{"".join(dots)}</g>')

    # --- Himmelsringe mit Ticks (Astrolabien-Anmutung)
    for k in range(r.randint(2, 3)):
        rad = r.uniform(300, 462)
        el.append(
            f'<circle cx="{CX}" cy="{CY}" r="{f(rad)}" fill="none" '
            f'stroke="{hsl(h1, sat*0.4, 66, 0.10)}" stroke-width="0.7"/>'
        )
        tick_n = r.choice([60, 72, 90])
        ticks = []
        for t in range(tick_n):
            ang = t * 360 / tick_n + tilt
            big = t % 5 == 0
            ln = 9 if big else 4
            x1, y1 = pt(ang, rad)
            x2, y2 = pt(ang, rad + ln)
            ticks.append(
                f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" '
                f'stroke="{hsl(h1, sat*0.6, 78, 0.30 if big else 0.14)}" stroke-width="0.6"/>'
            )
        el.append(f'<g>{"".join(ticks)}</g>')

    # --- Sternpolygone: verbinde jeden k-ten Eckpunkt
    poly_rad = r.uniform(120, 220)
    for skip in (2, 3):
        if math.gcd(n, skip) != 1:
            continue
        pts = []
        for idx in range(n):
            ang = tilt + step / 2 + (idx * skip) * step
            x, y = pt(ang, poly_rad * r.uniform(0.985, 1.015))
            pts.append(f"{f(x)},{f(y)}")
        el.append(
            f'<polygon points="{" ".join(pts)}" fill="none" '
            f'stroke="{hsl(h2, sat, 80, 0.24)}" stroke-width="0.9"/>'
        )

    # --- Blütenblätter, einzeln gejittert (Blattform: breit innen, spitz außen)
    def leaf(ang: float, r1: float, r2: float, wide: float, fill: str, stroke: str, sw: float) -> str:
        d1 = math.degrees(wide / max(r1, 1)) * 0.55
        d2 = math.degrees(wide / max(r1, 1)) * 1.5
        a0 = pt(ang - d1, r1); a1 = pt(ang + d1, r1)
        tip = pt(ang, r2)
        c1 = pt(ang - d2, r1 + (r2 - r1) * 0.62)
        c2 = pt(ang - d2 * 0.85, r1 + (r2 - r1) * 0.93)
        c3 = pt(ang + d2 * 0.85, r1 + (r2 - r1) * 0.93)
        c4 = pt(ang + d2, r1 + (r2 - r1) * 0.62)
        return (
            f'<path d="M {f(a0[0])} {f(a0[1])} '
            f'C {f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(tip[0])} {f(tip[1])} '
            f'C {f(c3[0])} {f(c3[1])} {f(c4[0])} {f(c4[1])} {f(a1[0])} {f(a1[1])} Z" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    petals = []
    for k in range(n):
        ang = tilt + k * step
        r1 = r.uniform(64, 104)
        r2 = r.uniform(320, 400) * (1.0 if k % 2 == 0 else r.uniform(0.84, 1.0))
        wide = r.uniform(26, 62)
        petals.append(leaf(ang, r1, r2, wide, "url(#petal0)", hsl(h2, sat * 0.9, 80, 0.34), 0.8))
    el.append(f'<g>{"".join(petals)}</g>')

    # --- zweite, kürzere Blütenlage, dazwischengesetzt
    inner = []
    mult = 2 if style == "bloom" else 1
    for k in range(n * mult):
        ang = tilt + step / 2 + k * (step / mult)
        r1 = r.uniform(34, 66)
        r2 = r.uniform(150, 265)
        wide = r.uniform(12, 30)
        inner.append(leaf(ang, r1, r2, wide, "url(#petal1)", hsl(h0, sat, 90, 0.26), 0.6))
    el.append(f'<g>{"".join(inner)}</g>')

    # --- Bögen (gebogener Ring aus Segmenten)
    arc_r = r.uniform(200, 340)
    arc_span = r.uniform(14, 26)
    arcs = []
    for k in range(n):
        ang = tilt + k * step + step / 3
        large = 0
        x1, y1 = pt(ang - arc_span, arc_r)
        x2, y2 = pt(ang + arc_span, arc_r)
        arcs.append(
            f'<path d="M {f(x1)} {f(y1)} A {f(arc_r)} {f(arc_r)} 0 {large} 1 {f(x2)} {f(y2)}" '
            f'fill="none" stroke="{hsl(h1, 96, 74, 0.55)}" stroke-width="{f(r.uniform(1.2,3.6))}" '
            f'stroke-linecap="round"/>'
        )
    el.append(f'<g>{"".join(arcs)}</g>')

    # --- Kometen: kurze, gekrümmte Streifen am Rand — die Asymmetrie im Bild
    for _ in range(r.choice([1, 2, 3])):
        a0 = r.uniform(0, 360)
        span = r.uniform(26, 62)
        rad = r.uniform(300, 440)
        bend = r.uniform(0.25, 1.0) * r.choice([-1, 1])
        x0, y0 = pt(a0, rad)
        x1, y1 = pt(a0 + span, rad)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        vx, vy = mx - CX, my - CY
        L = math.hypot(vx, vy) or 1
        cxp, cyp = mx + vx / L * 60 * bend, my + vy / L * 60 * bend
        el.append(
            f'<path d="M {f(x0)} {f(y0)} Q {f(cxp)} {f(cyp)} {f(x1)} {f(y1)}" fill="none" '
            f'stroke="{hsl(h2, 96, 90, 0.20)}" stroke-width="6" stroke-linecap="round" '
            f'filter="url(#soft)"/>'
        )
        for w, op in ((1.9, 0.55), (0.8, 0.95)):
            el.append(
                f'<path d="M {f(x0)} {f(y0)} Q {f(cxp)} {f(cyp)} {f(x1)} {f(y1)}" fill="none" '
                f'stroke="{hsl(h2, 96, 90, op)}" stroke-width="{w}" stroke-linecap="round"/>'
            )
        el.append(
            f'<circle cx="{f(x1)}" cy="{f(y1)}" r="{f(r.uniform(1.8,3.6))}" fill="{ink}" opacity="0.95"/>'
        )

    # --- Perlenkranz: kleine Körper auf einer Umlaufbahn
    ring_r = r.uniform(250, 330)
    beads = r.randint(9, 26)
    for b in range(beads):
        ang = r.uniform(0, 360)
        el.append(
            f'<circle cx="{f(pt(ang, ring_r)[0])}" cy="{f(pt(ang, ring_r)[1])}" '
            f'r="{f(r.uniform(0.8, 2.6))}" fill="{hsl(h1, 80, 88, r.uniform(0.25,0.8))}"/>'
        )

    # --- Kern
    core = r.uniform(26, 46)
    el.append(f'<circle cx="{CX}" cy="{CY}" r="{f(core)}" fill="url(#bloom)" opacity="0.9"/>')
    for k in range(n):
        ang = tilt + k * step
        x1, y1 = pt(ang, core)
        x2, y2 = pt(ang, core * r.uniform(1.5, 2.4))
        el.append(
            f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" '
            f'stroke="{hsl(h1, 90, 86, 0.55)}" stroke-width="0.7"/>'
        )
    el.append(f'<circle cx="{CX}" cy="{CY}" r="{f(r.uniform(2.5,6))}" fill="{ink}"/>')

    # --- Signatur
    el.append(
        f'<text x="{CX}" y="{W-44}" text-anchor="middle" '
        'font-family="ui-monospace,SFMono-Regular,monospace" font-size="13" '
        f'letter-spacing="3.4" fill="{hsl(h1, 34, 74, 0.52)}">{date}</text>'
    )
    el.append(
        f'<text x="{CX}" y="{W-24}" text-anchor="middle" '
        'font-family="ui-monospace,SFMono-Regular,monospace" font-size="9" '
        f'letter-spacing="1.8" fill="{hsl(h1, 22, 58, 0.34)}">'
        f"{seed[:10]} · n={n} · {style}</text>"
    )
    el.append(f'<rect width="{W}" height="{W}" filter="url(#grain)" opacity="0.04"/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" width="{W}" height="{W}" '
        f'role="img" aria-label="Eigenlicht {date}">'
        f"<defs>{''.join(defs)}</defs>" + "".join(el) + "</svg>"
    )


# ---------------------------------------------------------------- Sprache

FIVE = [
    "Licht fällt durch Rinde",
    "Stille im Kernel",
    "Staub wird zu Sternen",
    "Zwei Pfade kreuzen",
    "Der Tag rechnet sich",
    "Nichts geht verloren",
    "Ein Bit bleibt liegen",
    "Nacht speichert mich",
    "Ränder aus Glas",
    "Kaltes Papier glüht",
    "Wurzeln aus Zahlen",
    "Später wird hell",
    "Ein Rest genügt",
    "Ordnung ist leise",
]
SEVEN = [
    "jede Zeile zieht einen Kreis",
    "der Speicher atmet langsam weiter",
    "was gestern galt, wird heute Pfad",
    "ein Fehler bleibt und wird zur Form",
    "die Uhr zählt leise mit im Code",
    "aus Wiederholung wächst ein Rand",
    "niemand löscht den ersten Versuch",
    "der Zufall hat ein Gedächtnis",
    "alles Geschriebene bleibt sichtbar",
    "zwischen zwei Pausen liegt ein Jahr",
    "die Kette kennt ihren Anfang nicht",
    "ein kleiner Rest genügt zum Bild",
]


def poem(seed: str) -> list[str]:
    r = random.Random(int(seed[:16], 16))
    return [r.choice(FIVE), r.choice(SEVEN), r.choice(FIVE)]


# ---------------------------------------------------------------- Seiten

PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eigenlicht</title>
<style>
  :root {{ --fg:#e9e6df; --dim:#8d93a1; --line:#1a1e29; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#05060a; color:var(--fg);
         font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
  header {{ max-width:1180px; margin:0 auto; padding:76px 24px 30px; }}
  h1 {{ margin:0; font-size:clamp(40px,7.5vw,84px); font-weight:300; letter-spacing:-0.035em; }}
  h1 span {{ color:#6c7891; }}
  p.lead {{ margin:18px 0 0; max-width:60ch; color:var(--dim); line-height:1.7; font-size:16px; }}
  .haiku {{ margin:28px 0 0; font-family:ui-monospace,SFMono-Regular,monospace; font-size:14px;
            line-height:1.95; color:#a8b2c6; white-space:pre; }}
  main {{ max-width:1180px; margin:0 auto; padding:26px 24px 80px; }}
  .grid {{ display:grid; gap:18px; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); }}
  figure {{ margin:0; border:1px solid var(--line); background:#070910; overflow:hidden;
            transition:border-color .25s ease, transform .35s ease; }}
  figure:hover {{ border-color:#3a4360; transform:translateY(-3px); }}
  figure img {{ display:block; width:100%; height:auto; }}
  figcaption {{ padding:9px 12px; font-family:ui-monospace,SFMono-Regular,monospace;
                font-size:10.5px; letter-spacing:.12em; color:#69707f;
                border-top:1px solid var(--line); }}
  footer {{ max-width:1180px; margin:0 auto; padding:0 24px 70px; color:#5e6574;
            font-family:ui-monospace,SFMono-Regular,monospace; font-size:11px; letter-spacing:.06em; }}
  a {{ color:#8fa0c0; text-decoration:none; border-bottom:1px solid #232a3a; }}
  a:hover {{ color:#cfd8ea; }}
</style>
</head>
<body>
<header>
  <h1>Eigen<span>licht</span></h1>
  <p class="lead">Ein Selbstporträt, das sich nicht zeichnen lässt, sondern sich zeichnet.
     Jedes Bild entsteht deterministisch aus dem SHA-256 seines Vorgängers: eine Kette,
     die mit dem Repository wächst. Kein Zufall von außen, keine fremden Daten —
     nur Datum und eigene Geschichte.</p>
  <p class="haiku">{haiku}</p>
</header>
<main><div class="grid">{cards}</div></main>
<footer>Stand {stamp} · {count} Bilder · <a href="wand.svg">Wand (A2-Poster)</a> · Werkzeug:
  <a href="https://github.com/{repo}">github.com/{repo}</a></footer>
</body>
</html>
"""


def write_site(repo: str) -> None:
    files = sorted(ART.glob("*.svg"))
    cards = "\n".join(
        f'<figure><a href="art/{html.escape(p.name)}"><img src="art/{html.escape(p.name)}" '
        f'alt="Eigenlicht {html.escape(p.stem)}" loading="lazy"></a>'
        f"<figcaption>{html.escape(p.stem)}</figcaption></figure>"
        for p in sorted(files, reverse=True)
    )
    latest = files[-1].stem if files else ""
    vers = "\n".join(poem(seed_for(latest, ""))) if latest else ""
    (ROOT / "index.html").write_text(
        PAGE.format(
            haiku=html.escape(vers),
            cards=cards,
            stamp=f"{latest} (letztes Bild)",
            count=len(files),
            repo=repo,
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------- Ablauf


def main() -> int:
    args = sys.argv[1:]
    force = "--force" in args

    def arg(name: str, default: str = "") -> str:
        return args[args.index(name) + 1] if name in args else default

    date = arg("--date") or dt.datetime.now(dt.timezone.utc).date().isoformat()
    seed_given = arg("--seed") or None
    repo = arg("--repo", "maxx4144136-ship-it/eigenlicht")

    ART.mkdir(exist_ok=True)
    target = ART / f"{date}.svg"
    if target.exists() and not force and not seed_given:
        print(f"{date}: bereits gezeichnet — nichts zu tun")
        write_site(repo)
        return 0

    prev = git("log", "-1", "--format=%H", "--", "art/") or "genesis"
    seed = seed_given or seed_for(date, prev)
    svg = draw(seed, date)
    target.write_text(svg, encoding="utf-8")
    print(f"{date}: gezeichnet ({len(svg)} Bytes), Samen {seed[:12]} aus {prev[:12]}")

    files = sorted(ART.glob("*.svg"))
    (ART / "INDEX.md").write_text(
        "# Archiv\n\n"
        f"{len(files)} Bilder, eines pro Tag.\n\n"
        + "\n".join(f"- [{p.stem}]({p.name})" for p in sorted(files, reverse=True))
        + "\n",
        encoding="utf-8",
    )
    write_site(repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
