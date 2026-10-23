# SVGraft

**SVGraft** splits a large SVG file into a multipage PDF, tiling it across standard print pages with configurable margins and alignment corner marks. It is designed for printing oversized vector graphics (such as posters, banners, or blueprints) on ordinary home or office printers.

I developed the first version at an FRC competition to print a 25x30 poster for Engineering Inspiration judging on letter paper.

---

## Features

- Splits any SVG (with a viewBox defined in mm or in) into a grid of tiles that each fit on a single page
- Outputs a single merged PDF ready to print and assemble
- Configurable page size, margins, and tile orientation
- Automatic orientation optimization — chooses portrait or landscape to minimize page count
- Corner alignment marks on every tile to aid physical assembly
- Tile labels printed on each page for easier assembly ordering
- Progress display and tile summary table via `rich`
- **Scale control** — scale the output up or down before tiling, using percentage, target page count, or target physical dimensions
- **PDF input** — accepts PDF files directly as input (first page is converted and tiled)

---

## Requirements

- Python 3.9+
- [CairoSVG](https://cairosvg.org/) and its native Cairo library
- See `requirements.txt` for the full list of Python dependencies

Install system dependencies (Debian/Ubuntu):

```bash
sudo apt-get install libcairo2-dev
```

---

## Installation

```bash
pip install SVGraft
```

Or install it from source:

```bash
git clone https://github.com/deekb/SVGraft
cd SVGraft
pip install .
```

---

## Usage

### Command Line

```bash
svgraft [input_file] [options]
```

| Argument                    | Default               | Description                                                 |
|-----------------------------|-----------------------|-------------------------------------------------------------|
| `input_file`                | `./input.svg`         | Path to the input SVG or PDF file                           |
| `-o`, `--output`            | `./output_merged.pdf` | Path for the output PDF file                                |
| `--page-width`              | `8.5`                 | Page width in inches                                        |
| `--page-height`             | `11.0`                | Page height in inches                                       |
| `--margin`                  | `7.0`                 | Margin on each page in millimeters                          |
| `--scale`                   | —                     | Scale factor as a multiplier (`1.5`) or percentage (`150%`) |
| `--output-width`            | —                     | Target assembled width (e.g. `48in`, `1200mm`)              |
| `--output-height`           | —                     | Target assembled height (e.g. `36in`, `900mm`)              |
| `--pages-wide`              | —                     | Target number of tiles across                               |
| `--pages-tall`              | —                     | Target number of tiles tall                                 |
| `--no-optimize-orientation` | —                     | Disable automatic portrait/landscape optimization           |
| `--border-stroke`           | —                     | Border stroke width in SVG units                            |
| `--corner-stroke`           | —                     | Corner triangle stroke width in SVG units                   |

**Examples:**

Split a poster onto US Letter pages with default settings:
```bash
svgraft my_poster.svg
```

Use A4 pages with a 10 mm margin and a custom output path:
```bash
svgraft my_poster.svg --page-width 8.27 --page-height 11.69 --margin 10 -o poster_tiled.pdf
```

Scale the SVG to 150% of its native size before tiling:
```bash
svgraft my_poster.svg --scale 150%
```

Scale so the assembled output is exactly 4 feet wide:
```bash
svgraft my_poster.svg --output-width 48in
```

Tile the SVG to span exactly 3 pages wide:
```bash
svgraft my_poster.svg --pages-wide 3
```

Tile the first page of a PDF:
```bash
svgraft document.pdf --scale 200%
```

### Python API

```python
from svgraft.cli import split_svg
from svgraft.config import ProcessConfig

config = ProcessConfig(
    input_file="my_poster.svg",
    page_width_in=8.5,
    page_height_in=11.0,
    margin_mm=6.35,
    output_file="output.pdf",
    optimize_tile_orientation=True,
    scale_factor=1.5,      # optional: scale to 150%
    total_width_in=48.0,   # optional: target assembled width
    pages_wide=3,          # optional: target tile columns
)

with open(config.input_file, "rb") as f:
    split_svg(f, config)
```

---

## SVG Requirements

The input SVG **must** have:

- A `viewBox` attribute (e.g. `viewBox="0 0 1200 900"`)
- A `width` attribute defined in **inches** (`in`) or **millimeters** (`mm`)

Example SVG header:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 2400 1800"
     width="24in" height="18in"/>
```

---

## Scale Control

SVGraft can scale your SVG before tiling using any of three modes. All modes account for per-page margins when computing the final tile grid.

### Percentage / multiplier scaling

Scale the SVG up or down relative to its native size:

```bash
svgraft poster.svg --scale 150%
svgraft poster.svg --scale 0.75
```

### Target physical dimensions

Specify the desired real-world width or height of the assembled output. SVGraft derives the required scale factor from the SVG's native physical size:

```bash
svgraft poster.svg --output-width 48in
svgraft poster.svg --output-height 1200mm
```

Supported units: `in`, `mm`, `m`.

### Target page count

Specify how many tiles wide or tall the output should span. SVGraft back-calculates the scale factor to hit that grid exactly. Orientation optimization is disabled in this mode since you have expressed an explicit layout intent:

```bash
svgraft poster.svg --pages-wide 3
svgraft poster.svg --pages-tall 2
```

---

## PDF Input

SVGraft accepts PDF files as input in addition to SVG. The first page of the PDF is converted to SVG internally and run through the standard tiling pipeline:

```bash
svgraft document.pdf
svgraft document.pdf --scale 200% -o tiled_output.pdf
```

> **Note:** Only the first page of a multipage PDF is currently processed.

---

## How It Works

1. **Parse** the input file. SVG files are parsed directly; PDF inputs have their first page converted to SVG via PyMuPDF before continuing.
2. **Apply scaling** — if a scale mode is specified (`--scale`, `--output-width`, `--output-height`, `--pages-wide`, or `--pages-tall`), the units-per-inch value is adjusted so the scaled content maps correctly onto the tile grid.
3. **Compute tiles** — calculate the grid of columns and rows needed so each tile fits within the usable page area (page size minus margins).
4. **Optimize orientation** — if rotating tiles from portrait to landscape (or vice versa) produces fewer total pages, SVGraft automatically swaps the dimensions and re-tiles. Disabled when `--pages-wide` or `--pages-tall` is used.
5. **Render tiles** — for each grid cell, clip and translate the SVG, add corner alignment triangles, a dashed border, and a tile label, then render to PDF via CairoSVG.
6. **Merge** — all per-tile PDFs are merged into a single output PDF using pypdf.

---

## Assembly

Each page includes:

- **Corner triangles** at the four content corners for precise cut-and-align assembly
- A **dashed border** showing the exact content boundary
- A **tile label** (e.g. `Tile 0`, `Tile 1`, …) near the bottom-left corner for ordering pages during assembly

To assemble a print: trim half of the pages to their dashed border, then align them to the corner marks of the adjacent tiles.

---

## Configuration Defaults

Defaults are defined in `src/svgraft/config.py`:

| Setting                      | Default | Description                               |
|------------------------------|---------|-------------------------------------------|
| `DEFAULT_PAGE_WIDTH_IN`      | `8.5`   | Page width (inches)                       |
| `DEFAULT_PAGE_HEIGHT_IN`     | `11.0`  | Page height (inches)                      |
| `DEFAULT_MARGIN_MM`          | `7.0`   | Per-page margin                           |
| `DEFAULT_CORNER_TRIANGLE_MM` | `2.0`   | Size of corner alignment triangles        |
| `DEFAULT_CORNER_STROKE_MM`   | `0.1`   | Stroke width of corner marks              |
| `OPTIMIZE_TILE_ORIENTATION`  | `True`  | Auto-flip orientation for fewer pages     |

---

## Running Tests

```bash
pip install pdf2image
python -m unittest tests/testSVGraft.py
```

The test splits `tests/data/test_poster.svg` onto US Letter pages and verifies the output PDF is created.

---

## Project Structure

```
SVGraft/
├── src/svgraft/
│   ├── cli.py          # Entry point: argument parsing and split_svg()
│   ├── config.py       # Default settings and ProcessConfig
│   ├── tiling.py       # Tile grid computation
│   ├── rendering.py    # Per-tile SVG manipulation and PDF rendering
│   ├── pdf.py          # In-memory PDF merging and PDF-to-SVG conversion
│   ├── svg_io.py       # SVG unit parsing and physical dimension conversion
│   ├── geometry.py     # Unit conversion utilities
│   └── debug.py        # Debug/console helpers
├── tests/
│   ├── data/test_poster.svg
│   └── testSVGraft.py
├── pyproject.toml
└── requirements.txt
```

---

## License

This project is licensed under the **GNU General Public License v3.0 or later**. See [LICENSE](LICENSE) for details.

---

## Author

Derek Baier — [derek.m.baier@gmail.com](mailto:derek.m.baier@gmail.com)
