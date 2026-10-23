import argparse
import io
from copy import deepcopy
from pathlib import Path

from lxml import etree
from rich.table import Table
from rich.progress import track

from .geometry import mm_to_units
from .config import ProcessConfig, MM_PER_INCH
from .debug import debug, console
from .svg_io import get_units_per_inch, convert_to_inches
from .tiling import compute_tiles
from .rendering import make_tile
from .pdf import merge_pdfs_in_memory, pdf_to_svg_first_page
from .util import count_not_none


class ViewBox:
    min_x: int
    min_y: int
    width: int
    height: int

    def __init__(self, min_x, min_y, width, height, units_per_inch):
        self.min_x = min_x
        self.min_y = min_y
        self.width = width
        self.height = height
        self.units_per_inch = units_per_inch

    def get_width_svg_units(self):
        return self.width / self.units_per_inch

    def get_height_svg_units(self):
        return self.height / self.units_per_inch


class PageLayout:
    def __init__(self, page_width_in, page_height_in, margin_mm):
        self.page_width_in = page_width_in
        self.page_height_in = page_height_in
        self.margin_mm = margin_mm

    @property
    def margin_allowance_inches(self):
        return 2 * self.margin_mm / MM_PER_INCH

    def usable_width_in(self):
        return self.page_width_in - self.margin_allowance_inches

    def usable_height_in(self):
        return self.page_height_in - self.margin_allowance_inches

    def flipped(self):
        """Return a new layout with width and height swapped."""
        return PageLayout(self.page_height_in, self.page_width_in, self.margin_mm)


class TilingResult:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows

    def page_count(self):
        return self.cols * self.rows

    def is_more_efficient_than(self, other):
        return self.page_count() < other.page_count()


class Tile:
    def __init__(self, tile_id, row, col, x, y, actual_w, actual_h):
        self.tile_id = tile_id
        self.row = row
        self.col = col
        self.x = x
        self.y = y
        self.actual_w = actual_w
        self.actual_h = actual_h

    def table_row(self):
        return [str(self.tile_id), str(self.row), str(self.col), str(round(mm_to_units(self.actual_w, 1), 4)),
                str(round(mm_to_units(self.actual_h, 1), 4))]


def get_orientation_descriptor(x, y):
    if abs(x - y) < 1e-6:
        return "square"
    return "portrait" if y > x else "landscape"


def split_svg(svg_file_like_object, config, _already_optimized=False):
    debug("SVGraft initialized with config", config.__dict__)

    tree = etree.parse(svg_file_like_object)
    root = tree.getroot()

    units_per_inch = get_units_per_inch(root)

    view_box = root.get("viewBox")
    view_box = ViewBox(*map(float, view_box.split()), units_per_inch)

    debug("SVG loaded")

    layout = PageLayout(config.page_width_in, config.page_height_in, config.margin_mm)

    if config.scale_factor is not None:
        scale_factor = config.scale_factor
    elif config.total_width_in is not None:
        scale_factor = config.total_width_in / view_box.get_width_svg_units()
    elif config.total_height_in is not None:
        scale_factor = config.total_height_in / view_box.get_height_svg_units()
    elif config.pages_wide is not None:
        margin_total_in = layout.margin_allowance_inches * config.pages_wide
        scale_factor = ((config.pages_wide * layout.page_width_in) - margin_total_in) / view_box.get_width_svg_units()
        _already_optimized = True
    elif config.pages_tall is not None:
        margin_total_in = layout.margin_allowance_inches * config.pages_tall
        scale_factor = ((config.pages_tall * layout.page_height_in) - margin_total_in) / view_box.get_height_svg_units()
        _already_optimized = True
    else:
        scale_factor = 1

    if scale_factor is not None:
        units_per_inch /= scale_factor
        debug(f"Applying scaling factor: {scale_factor} new UPI: {units_per_inch}")

    clip_w = layout.usable_width_in() * units_per_inch
    clip_h = layout.usable_height_in() * units_per_inch

    debug("Computing tiling")
    tiling = TilingResult(*compute_tiles(view_box.width, view_box.height, clip_w, clip_h))
    if not _already_optimized:
        debug("Computing tiling rotated")
        tiling_rotated = TilingResult(*compute_tiles(view_box.width, view_box.height, clip_h, clip_w))
        debug("Optimizing for least pages used")
        if tiling_rotated.is_more_efficient_than(tiling):
            previous_rotation = get_orientation_descriptor(clip_w, clip_h)
            new_rotation = get_orientation_descriptor(clip_h, clip_w)
            debug(f"Rotating tiles to {new_rotation} found to be more efficient, "
                  f"uses {tiling_rotated.page_count()} pages {new_rotation} "
                  f"instead of {tiling.page_count()} pages {previous_rotation}", color="green")
            if config.optimize_tile_orientation:
                debug(f"Rerunning split_svg with optimized rotation", color="green")
                config.page_width_in, config.page_height_in = config.page_height_in, config.page_width_in
                flipped_config = deepcopy(config)
                flipped_config.page_width_in, flipped_config.page_height_in = config.page_height_in, config.page_width_in
                svg_file_like_object.seek(0)
                return split_svg(svg_file_like_object, config, _already_optimized=True)
            else:
                debug("Consider enabling optimize_tile_orientation or flipping the tile width and height",
                      color="yellow")

    pages = []
    tile_id = 0

    table = Table(title="Tiles")
    table.add_column("id")
    table.add_column("row")
    table.add_column("col")
    table.add_column("actual_w")
    table.add_column("actual_h")

    for row in track(range(tiling.rows)):
        for col in range(tiling.cols):
            x = view_box.min_x + col * clip_w
            y = view_box.min_y + row * clip_h

            actual_w = min(clip_w, (view_box.min_x + view_box.width) - x)
            actual_h = min(clip_h, (view_box.min_y + view_box.height) - y)

            if actual_w <= 0 or actual_h <= 0:
                continue

            tile = Tile(tile_id, row, col, x, y, actual_w, actual_h)
            table.add_row(*tile.table_row())

            pages.append(
                make_tile(tree, tile.x, tile.y, tile.actual_w, tile.actual_h, tile.tile_id, units_per_inch, config))

            tile_id += 1

    console.print(table)

    with open(config.output_file, "wb") as f:
        f.write(merge_pdfs_in_memory(pages))

    return None


def main():
    parser = argparse.ArgumentParser(description="Split an SVG into tiled PDF pages")

    parser.add_argument("input_file", nargs="?", default=None, help="Input SVG file")

    parser.add_argument("-o", "--output", dest="output_file", default=None, help="Output PDF file")

    parser.add_argument("--page-width", type=float, default=None, help="Page width (inches)")

    parser.add_argument("--page-height", type=float, default=None, help="Page height (inches)")

    parser.add_argument("--margin", type=float, default=None, help="Margin (mm)")

    parser.add_argument("--scale", type=str, default=None, help="Scaling factor")

    parser.add_argument("--output-width", type=str, default=None, help="Width in inches")

    parser.add_argument("--output-height", type=str, default=None, help="Height in inches")

    parser.add_argument("--pages-wide", type=int, default=None, help="Pages wide")

    parser.add_argument("--pages-tall", type=int, default=None, help="Pages tall")

    parser.add_argument("--border-stroke", type=float, default=None, help="Border stroke in SVG units")

    parser.add_argument("--corner-stroke", type=float, default=None, help="Corner triangle stroke in SVG units")

    parser.add_argument("--no-optimize-orientation", default=None, action='store_true',
                        help="Disable automatic portrait/landscape optimization")

    args = parser.parse_args()

    if not Path(args.input_file).is_file():
        print("ERROR: Input file {args.input_file} does not exist")

    if count_not_none(
            [args.page_height,
             args.page_width,
             args.output_width,
             args.output_height,
             args.pages_wide,
             args.pages_tall]) > 1:
        print("ERROR: More than one mutually exclusive argument provided")
        print("Only one of --page-width, --page-height, --output-width, --output-height, --pages-wide, --pages-tall can be specified")

    if args.output_width:
        output_width = convert_to_inches(args.output_width)
    else:
        output_width = None

    if args.output_height:
        output_height = convert_to_inches(args.output_height)
    else:
        output_height = None

    scale = args.scale

    if scale:
        if "%" in scale:
            scale = float(scale.rstrip(" %")) / 100.0
        else:
            scale = float(scale.strip())

    config = ProcessConfig(page_width_in=args.page_width, page_height_in=args.page_height, total_width_in=output_width,
        total_height_in=output_height, pages_wide=args.pages_wide, pages_tall=args.pages_tall, scale_factor=scale,
        optimize_tile_orientation=not args.no_optimize_orientation, margin_mm=args.margin, corner_triangle_size_mm=2.0,
        corner_triangle_stroke=args.corner_stroke, border_stroke_mm=args.border_stroke, input_file=args.input_file,
        output_file=args.output_file)

    if config.input_file.endswith(".svg"):
        svg_file_like_object = open(config.input_file, "rb")
    elif config.input_file.endswith(".pdf"):
        svg_file_like_object = io.BytesIO(pdf_to_svg_first_page(open(config.input_file, "rb").read()).encode())
    else:
        svg_file_like_object = open(config.input_file, "rb")

    split_svg(svg_file_like_object, config)
    svg_file_like_object.close()


if __name__ == "__main__":
    main()
