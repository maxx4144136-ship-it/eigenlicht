#!/usr/bin/env python3
"""
Die Wand — legt das Archiv als druckbares Poster aus.

Standard: A2 hochkant, 30 Bilder in gleichmäßigem Abstand über das Archiv
verteilt (bei weniger als 30 Bildern: alle). Die Bilder werden als
data:-URI eingebettet, damit keine Gradient-IDs kollidieren und das Poster
eine einzige transportierbare Datei bleibt.

Aufruf:
    python3 wall.py                       # wand.svg, A2, max. 30 Bilder
    python3 wall.py --format a3 --max 20
    python3 wall.py --out /tmp/wand.svg
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
ART = ROOT / "art"

# mm
FORMATS = {"a4": (210, 297), "a3": (297, 420), "a2": (420, 594), "a1": (594, 841)}

INK = "#e9e6df"
DIM = "#7f8697"
LINE = "#232838"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pick(files: list[pathlib.Path], maximum: int) -> list[pathlib.Path]:
    """Gleichmäßig über das Archiv verteilt, nicht nur die letzten N."""
    if len(files) <= maximum:
        return files
    step = (len(files) - 1) / (maximum - 1)
    return [files[round(i * step)] for i in range(maximum)]


def grid_shape(n: int, w: float, h: float) -> tuple[int, int]:
    """Spalten/Zeilen, die quadratische Zellen möglichst groß machen."""
    best = (1, n)
    best_size = 0.0
    for cols in range(1, n + 1):
        rows = -(-n // cols)
        size = min(w / cols, h / rows)
        if size > best_size:
            best_size, best = size, (cols, rows)
    return best


def build(files: list[pathlib.Path], fmt: str, maximum: int) -> str:
    pw, ph = FORMATS[fmt]
    chosen = pick(files, maximum)
    n = len(chosen)

    m = 20.0 if fmt in ("a1", "a2") else 14.0          # Rand
    header = 70.0 if fmt in ("a1", "a2") else 46.0
    footer = 22.0
    gap = 4.0 if fmt in ("a1", "a2") else 2.5
    cap = 5.0 if fmt in ("a1", "a2") else 3.6

    ax, ay = m, m + header
    aw, ah = pw - 2 * m, ph - m - footer - (m + header)

    cols, rows = grid_shape(n, aw, ah)
    cell = min((aw - gap * (cols - 1)) / cols,
               (ah - (gap + cap) * (rows - 1)) / rows)
    total_w = cols * cell + gap * (cols - 1)
    total_h = rows * (cell + cap) + gap * (rows - 1)
    ox = ax + (aw - total_w) / 2
    oy = ay + (ah - total_h) / 2

    out: list[str] = []
    out.append(f'<rect width="{pw}" height="{ph}" fill="#05060a"/>')

    # Kopf
    out.append(
        f'<text x="{m}" y="{m + 26}" font-family="ui-sans-serif,Helvetica,Arial,sans-serif" '
        f'font-size="{26 if fmt in ("a1","a2") else 17}" font-weight="300" letter-spacing="6" '
        f'fill="{INK}">EIGENLICHT</text>'
    )
    out.append(
        f'<text x="{m}" y="{m + 40}" font-family="ui-monospace,monospace" '
        f'font-size="{7 if fmt in ("a1","a2") else 4.6}" letter-spacing="2.6" fill="{DIM}">'
        f"DIE WAND · {n} BILDER · {esc(chosen[0].stem)} – {esc(chosen[-1].stem)}</text>"
    )
    out.append(
        f'<line x1="{m}" y1="{m + header - 12}" x2="{pw - m}" y2="{m + header - 12}" '
        f'stroke="{LINE}" stroke-width="0.4"/>'
    )

    # Bilder
    for idx, p in enumerate(chosen):
        c, r = idx % cols, idx // cols
        x = ox + c * (cell + gap)
        y = oy + r * (cell + cap + gap)
        data = base64.b64encode(p.read_bytes()).decode()
        out.append(
            f'<image x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" '
            f'preserveAspectRatio="xMidYMid meet" href="data:image/svg+xml;base64,{data}"/>'
        )
        out.append(
            f'<line x1="{x:.2f}" y1="{y + cell:.2f}" x2="{x + cell:.2f}" y2="{y + cell:.2f}" '
            f'stroke="{LINE}" stroke-width="0.3"/>'
        )
        out.append(
            f'<text x="{x:.2f}" y="{y + cell + cap * 0.78:.2f}" font-family="ui-monospace,monospace" '
            f'font-size="{cap * 0.62:.2f}" letter-spacing="{cap * 0.16:.2f}" fill="{DIM}">'
            f"{esc(p.stem)}</text>"
        )

    # Fuß
    out.append(
        f'<line x1="{m}" y1="{ph - m - 12}" x2="{pw - m}" y2="{ph - m - 12}" '
        f'stroke="{LINE}" stroke-width="0.4"/>'
    )
    out.append(
        f'<text x="{m}" y="{ph - m - 4}" font-family="ui-monospace,monospace" '
        f'font-size="{4.8 if fmt in ("a1","a2") else 3.2}" letter-spacing="1.1" fill="{DIM}">'
        "sha256(DATUM + VORGÄNGER-HASH)</text>"
    )
    out.append(
        f'<text x="{pw - m}" y="{ph - m - 4}" text-anchor="end" font-family="ui-monospace,monospace" '
        f'font-size="{4.8 if fmt in ("a1","a2") else 3.2}" letter-spacing="1.1" fill="{DIM}">'
        "github.com/maxx4144136-ship-it/eigenlicht</text>"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{pw}mm" height="{ph}mm" viewBox="0 0 {pw} {ph}" '
        f'role="img" aria-label="Eigenlicht Wand, {n} Bilder">'
        + "".join(out)
        + "</svg>"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", default="a2", choices=sorted(FORMATS))
    ap.add_argument("--max", type=int, default=30, dest="maximum")
    ap.add_argument("--out", default=str(ROOT / "wand.svg"))
    ap.add_argument("--all", action="store_true", help="alle Bilder statt max. N")
    a = ap.parse_args()

    files = sorted(ART.glob("*.svg"))
    if not files:
        print("Kein Archiv gefunden — erst generate.py laufen lassen.")
        return 1
    if a.all:
        a.maximum = len(files)

    svg = build(files, a.format, a.maximum)
    pathlib.Path(a.out).write_text(svg, encoding="utf-8")
    n = min(len(files), a.maximum)
    print(f"{a.format.upper()}: {n} von {len(files)} Bildern → {a.out} "
          f"({len(svg)/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
