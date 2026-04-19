# SVGraft

**SVGraft** splits a large SVG file into a multipage PDF, tiling it across standard print pages with configurable margins and alignment corner marks. It is designed for printing oversized vector graphics — such as posters, banners, or blueprints — on ordinary home or office printers.

I developed the first version at an FRC competition to print a 25x30 poster for Engineering Inspiration judging on letter paper.

---

## Features

- Splits any SVG (with a viewBox defined in mm or in) into a grid of tiles that each fit on a single page
- Outputs a single merged PDF ready to print and assemble
- Configurable page size, margins, and tile orientation
- Automatic orientation optimization — chooses portrait or landscape to minimize page count
- Corner alignment marks on every tile to aid physical assembly
- Progress display and tile summary table via `rich`

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

| Argument         | Default               | Description                        |
|------------------|-----------------------|------------------------------------|
| `input_file`     | `./input.svg`         | Path to the input SVG file         |
| `-o`, `--output` | `./output_merged.pdf` | Path for the output PDF file       |
| `--page-width`   | `8.5`                 | Page width in inches               |
| `--page-height`  | `11.0`                | Page height in inches              |
| `--margin`       | `5.0`                 | Margin on each page in millimeters |

**Examples:**

Split a poster onto US Letter pages with default settings:
```bash
svgraft my_poster.svg
```

Use A4 pages with a 10 mm margin and a custom output path:
```bash
svgraft my_poster.svg --page-width 8.27 --page-height 11.69 --margin 10 -o poster_tiled.pdf
```

### Python API

```python
from svgraft.cli import split_svg

split_svg(
    input_file="my_poster.svg",
    page_width_in=8.5,
    page_height_in=11.0,
    margin_mm=6.35,
    output_file="output.pdf",
    optimize_tile_orientation=True,
)
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

## How It Works

1. **Parse** the SVG and read its `viewBox` and physical dimensions to determine the internal units-per-inch scale.
2. **Compute tiles** — calculate the grid of columns and rows needed so each tile fits within the usable page area (page size minus margins).
3. **Optimize orientation** — if rotating tiles from portrait to landscape (or vice versa) produces fewer total pages, SVGraft automatically swaps the dimensions and re-tiles.
4. **Render tiles** — for each grid cell, clip and translate the SVG, add corner alignment triangles and a dashed border, then render to PDF via CairoSVG.
5. **Merge** — all per-tile PDFs are merged into a single output PDF using pypdf.

---

## Assembly

Each page includes:

- **Corner triangles** at the four content corners for precise cut-and-align assembly
- A **dashed border** showing the exact content boundary

To assemble a print: trim half of the pages to their dashed border, then align them to the corner marks of the adjacent tiles.

---

## Configuration Defaults

Defaults are defined in `src/svgraft/config.py`:

| Setting                      | Default | Description                           |
|------------------------------|---------|---------------------------------------|
| `DEFAULT_PAGE_WIDTH_IN`      | `8.5`   | Page width (inches)                   |
| `DEFAULT_PAGE_HEIGHT_IN`     | `11.0`  | Page height (inches)                  |
| `DEFAULT_MARGIN_MM`          | `5.0`   | Per-page margin                       |
| `DEFAULT_CORNER_TRIANGLE_MM` | `5`     | Size of corner alignment triangles    |
| `DEFAULT_CORNER_STROKE_MM`   | `0.1`   | Stroke width of corner marks          |
| `OPTIMIZE_TILE_ORIENTATION`  | `True`  | Auto-flip orientation for fewer pages |

---

## Running Tests

```bash
pip install pdf2image
python -m unittest tests/testSVGraft.py
```

The test is currently quite simple and splits `tests/input/test_poster.svg` onto US Letter pages and verifies the output PDF is created.

---

## Project Structure

```
SVGraft/
├── src/svgraft/
│   ├── cli.py          # Entry point: argument parsing and split_svg()
│   ├── config.py       # Default settings
│   ├── tiling.py       # Tile grid computation
│   ├── rendering.py    # Per-tile SVG manipulation and PDF rendering
│   ├── pdf.py          # In-memory PDF merging
│   ├── svg_io.py       # SVG unit parsing
│   ├── geometry.py     # Unit conversion utilities
│   └── debug.py        # Debug/console helpers
├── tests/
│   ├── input/test_poster.svg
│   ├── output/
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