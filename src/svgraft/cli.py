import argparse

from lxml import etree
from rich.table import Table
from rich.progress import track

from .geometry import mm_to_units
from .config import *
from .debug import debug, console
from .svg_io import get_units_per_inch
from .tiling import compute_tiles
from .rendering import make_tile
from .pdf import merge_pdfs_in_memory


def split_svg(input_file=DEFAULT_INPUT_FILE, page_width_in=DEFAULT_PAGE_WIDTH_IN, page_height_in=DEFAULT_PAGE_HEIGHT_IN,
              margin_mm=DEFAULT_MARGIN_MM, output_file=DEFAULT_OUTPUT_FILE,
              optimize_tile_orientation=OPTIMIZE_TILE_ORIENTATION, optimization_metric=OPTIMIZATION_METRIC,
              _already_optimized=False):
    debug("SVGraft initialized", locals())

    tree = etree.parse(input_file)
    root = tree.getroot()

    view_box = root.get("viewBox")
    minx, miny, total_w, total_h = map(float, view_box.split())

    debug("SVG loaded")

    units_per_inch = get_units_per_inch(root)

    margin_allowance_inches = (2 * margin_mm / MM_PER_INCH)

    usable_w_in = page_width_in - margin_allowance_inches
    usable_h_in = page_height_in - margin_allowance_inches

    clip_w = usable_w_in * units_per_inch
    clip_h = usable_h_in * units_per_inch

    debug("Computing tiling")
    cols, rows = compute_tiles(total_w, total_h, clip_w, clip_h)
    if not _already_optimized:
        debug("Computing tiling rotated")
        cols_if_rotated, rows_if_rotated = compute_tiles(total_w, total_h, clip_h, clip_w)
        debug("Optimizing for least pages used")
        if (cols_if_rotated * rows_if_rotated) < (cols * rows):
            previous_rotation = "portrait" if clip_h > clip_w else "landscape"
            new_rotation = "portrait" if clip_w > clip_h else "landscape"
            debug(f"Rotating tiles to {new_rotation} found to be more efficient, "
                  f"uses {cols_if_rotated * rows_if_rotated} pages {new_rotation} "
                  f"instead of {cols * rows} pages {previous_rotation}")
            if optimize_tile_orientation:
                debug(f"Rerunning split_svg with optimized rotation")
                # Many things must be recomputed to change the page width and height,
                # instead of doing this manually causing code duplication, we simply swap the width and height arguments and recurse
                return split_svg(input_file=input_file, page_width_in=page_height_in, page_height_in=page_width_in,
                                 margin_mm=margin_mm, output_file=output_file, _already_optimized=True)
            else:
                debug("Consider enabling optimize_tile_orientation or flipping the tile width and height")

    pdfs = []
    tile_id = 0

    table = Table(title="Tiles")
    table.add_column("id")
    table.add_column("row")
    table.add_column("col")
    table.add_column("actual_w")
    table.add_column("actual_h")

    for row in track(range(rows)):
        for col in range(cols):
            x = minx + col * clip_w
            y = miny + row * clip_h

            actual_w = min(clip_w, (minx + total_w) - x)
            actual_h = min(clip_h, (miny + total_h) - y)

            if actual_w <= 0 or actual_h <= 0:
                continue

            table.add_row(str(tile_id), str(row), str(col), str(round(mm_to_units(actual_w, 1), 4)),
                          str(round(mm_to_units(actual_h, 1), 4)))

            pdfs.append(
                make_tile(tree, x, y, actual_w, actual_h, tile_id, units_per_inch, page_width_in, page_height_in))

            tile_id += 1

    console.print(table)

    with open(output_file, "wb") as f:
        f.write(merge_pdfs_in_memory(pdfs))

    def truncate(value):
        if len(str(value)) > 256:
            value = str(value)[:256] + "..."
        return value

    debug("SVGraft finished", {key: truncate(value) for key, value in locals().items()})

    return None


def main():
    parser = argparse.ArgumentParser(description="Split an SVG into tiled PDF pages")

    parser.add_argument("input_file", nargs="?", default=DEFAULT_INPUT_FILE, help="Input SVG file")

    parser.add_argument("-o", "--output", dest="output_file", default=DEFAULT_OUTPUT_FILE, help="Output PDF file")

    parser.add_argument("--page-width", type=float, default=DEFAULT_PAGE_WIDTH_IN, help="Page width (inches)")

    parser.add_argument("--page-height", type=float, default=DEFAULT_PAGE_HEIGHT_IN, help="Page height (inches)")

    parser.add_argument("--margin", type=float, default=DEFAULT_MARGIN_MM, help="Margin (mm)")

    args = parser.parse_args()

    split_svg(input_file=args.input_file, page_width_in=args.page_width, page_height_in=args.page_height,
              margin_mm=args.margin, output_file=args.output_file)


if __name__ == "__main__":
    main()
