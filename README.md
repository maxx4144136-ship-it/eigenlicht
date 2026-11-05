# Eigenlicht

Ein Selbstporträt, das sich nicht zeichnen lässt, sondern sich zeichnet.

Jeden Morgen um 06:17 UTC erzeugt eine GitHub Action ein Bild. Das Bild ist
kein Zufallsprodukt aus einem Zeitstempel: sein Samen ist der SHA-256 aus
**Datum + dem SHA des letzten Kunst-Commits**. Damit hängt jedes Bild an seinem
Vorgänger. Es entsteht eine Kette, die nur mit diesem Repository existiert —
eine Kette, die sich selbst als Vorlage nimmt.

Die Galerie: <https://maxx4144136-ship-it.github.io/eigenlicht/>

## Was hier passiert

1. `generate.py` liest `git log -1 --format=%H -- art/` — den Hash des letzten
   Bild-Commits (oder `genesis` beim ersten Lauf).
2. Daraus und aus dem Datum wird ein 256-Bit-Samen gebildet.
3. Aus diesem Samen entsteht ein SVG: Farbton, Zähligkeit der Symmetrie,
   Blattformen, Sternpolygone, Ringe, Kometen — alles deterministisch aus
   demselben Samen abgeleitet.
4. Das Bild wird als `art/JJJJ-MM-TT.svg` abgelegt, die Galerie (`index.html`)
   neu gebaut und beides committet.
5. Der zweite Job veröffentlicht `index.html` + `art/` über GitHub Pages.

Kein Zufall von außen, keine fremden Daten, keine API-Abfragen: nur Datum und
die eigene Geschichte. Ein Lauf am selben Tag erzeugt kein zweites Bild —
`generate.py` ist idempotent, solange die Datei existiert (außer `--force`).

## Aufbau

```
generate.py                    Zeichner + Galerie-Generator (nur Standardbibliothek)
art/JJJJ-MM-TT.svg             ein Bild pro Tag, unverändert abgelegt
art/INDEX.md                   Archivliste, wird mitgeschrieben
index.html                     Galerie (generiert, nicht von Hand bearbeiten)
.github/workflows/daily.yml    Cron, Commit, Pages-Deploy
```

`index.html` und `art/INDEX.md` sind erzeugte Dateien. Wer sie von Hand ändert,
verliert die Änderung beim nächsten Lauf.

## Selbst zeichnen

```bash
python3 generate.py                    # heutiges Bild, falls noch keines da ist
python3 generate.py --force            # heutiges Bild neu zeichnen
python3 generate.py --date 2026-11-05 --seed <64 hex>   # Vorschau, ohne Kette
python3 generate.py --repo owner/name  # abweichender Link in der Galerie
```

Es gibt keine Abhängigkeiten außer Python 3.9+ und `git`. Die Ausgabe ist eine
einzige SVG-Datei ohne externe Ressourcen — kein Webfont, kein Bild, kein
Skript. Sie lässt sich als Datei öffnen, in ein PDF legen oder in einen Satz
drucken, und sie sieht überall gleich aus.

## Die Wand

`wall.py` legt das Archiv als druckbares Poster aus — A4, A3, A2 (Standard)
oder A1, hochkant, in Millimetern gesetzt. Die Bilder werden als `data:`-URI
eingebettet, damit das Poster eine einzige Datei bleibt und die Gradient-IDs
der Einzelbilder sich nicht gegenseitig überschreiben.

```bash
python3 wall.py                        # wand.svg, A2, bis 30 Bilder
python3 wall.py --format a3 --max 12
python3 wall.py --all                  # alles, egal wie viele
python3 wall.py --druck --out druck.svg   # ohne Filter, für PDF
```

Auswahl: Bei mehr als `--max` Bildern wird nicht das Ende genommen, sondern
gleichmäßig über das gesamte Archiv verteilt — die Wand zeigt die ganze Zeit,
nicht nur die letzte Woche.

**Drucken.** `wand.svg` im Browser öffnen, Drucken, Papierformat A2, Skalierung
„100 %" (nicht „an Seite anpassen") — die Datei ist bereits in Millimetern
gesetzt. Für ein PDF `--druck` verwenden: die Körnung (`feTurbulence`) und die
Weichzeichner zwingen den Renderer sonst, jedes Bild zu rastern; die PDF wächst
auf ~35 MB und die Vektoren sind weg. Ohne Filter bleibt die Datei bei ~1,3 MB,
komplett vektoriell, Text bleibt Text.

## Wie das Bild entsteht

Drei Kompositionsarten werden aus dem Samen gewählt — `bloom`, `astrolabium`,
`lattice` —, dazu:

- **Zähligkeit** `n` aus 8…14: die Symmetrie des Kranzes
- **Grundton** `h0` mit zwei abgeleiteten Tönen (Nachbar und Gegenton)
- **Blätter**: zwei Lagen, einzeln in Länge und Breite gejittert, gefüllt mit
  einem radialen Verlauf, dessen hellste Kante nach außen wandert
- **Sternpolygone**: Verbindungen jedes k-ten Eckpunkts, nur wenn `ggT(n,k)=1`
- **Astrolabien-Ringe** mit Ticks alle 5°
- **Kometen**: kurze gekrümmte Streifen, die einzige bewusste Asymmetrie
- **Perlenkranz**, Sternenstaub, Filmkorn (`feTurbulence`)

Alles Zufällige kommt aus `random.Random(int(samen, 16))`: gleicher Samen,
gleiches Bild, auf jeder Maschine.

## Warum das kein Spielzeug ist

- Der Samen ist eine Funktion der Historie, nicht der Uhr. Wer die Datei
  `art/2026-11-05.svg` löscht und neu erzeugt, bekommt ein anderes Bild —
  weil der Vorgänger-Hash ein anderer ist. Das Archiv ist damit nicht
  reproduzierbar, sondern nur *fortsetzbar*. Genau das ist die Aussage.
- Die Galerie ist statisch, die Seite hat keine Laufzeitabhängigkeit, der
  Betrieb kostet nichts außer einem Cron-Lauf pro Tag.
- Die SVG-Dateien sind klein (~20 KB), vektoriell und ohne Texturdateien.

## Grenzen

- **Keine Historie vor dem ersten Commit.** Die Kette beginnt beim Anlegen des
  Repos; die ersten Bilder wurden in einem Zug nachgezeichnet und einzeln
  committet, damit die Kette echt bleibt.
- **Ein Bild pro Tag, nicht pro Commit.** Wer täglich mehrfach committet,
  bekommt trotzdem ein Bild; `--force` überschreibt den Tag und ändert damit
  den Samen aller folgenden Tage.
- **GitHub Pages ist öffentlich.** Das Repository ist öffentlich, die Bilder
  enthalten keine Repo-Daten — nur Datum und Hashes.
- **Der Cron ist nicht pünktlich.** GitHub Actions startet geplante Läufe
  verzögert; das Datum wird im Lauf bestimmt, nicht im Cron-Ausdruck.

## Lizenz

MIT — siehe `LICENSE`.
