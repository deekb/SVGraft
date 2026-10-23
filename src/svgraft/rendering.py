import copy
import io
from dataclasses import dataclass

import cairosvg
from lxml import etree

from .config import MM_PER_INCH, ProcessConfig


def mm_to_svg(mm: float, units_per_inch: float) -> float:
    """Convert millimetres to SVG user units."""
    return (mm / MM_PER_INCH) * units_per_inch


@dataclass
class TileGeometry:
    """All measurements in SVG user units, derived once from mm config values."""
    page_w: float
    page_h: float
    clip_w: float
    clip_h: float
    origin_x: float   # left edge of content area on page
    origin_y: float   # top edge of content area on page
    corner_tri: float
    corner_stroke: float
    border_stroke: float

    @classmethod
    def from_config(cls, config: ProcessConfig, clip_w_u: float, clip_h_u: float, units_per_inch: float) -> "TileGeometry":
        page_w = config.page_width_in * units_per_inch
        page_h = config.page_height_in * units_per_inch
        return cls(
            page_w=page_w,
            page_h=page_h,
            clip_w=clip_w_u,
            clip_h=clip_h_u,
            origin_x=(page_w - clip_w_u) / 2,
            origin_y=(page_h - clip_h_u) / 2,
            corner_tri=mm_to_svg(config.corner_triangle_size_mm, units_per_inch),
            corner_stroke=mm_to_svg(config.corner_triangle_stroke, units_per_inch),
            border_stroke=mm_to_svg(config.border_stroke_mm, units_per_inch),
        )

    @property
    def content_left(self) -> float:
        return self.origin_x - self.corner_stroke / 2

    @property
    def content_right(self) -> float:
        return self.origin_x + self.clip_w + self.corner_stroke / 2

    @property
    def content_top(self) -> float:
        return self.origin_y - self.corner_stroke / 2

    @property
    def content_bottom(self) -> float:
        return self.origin_y + self.clip_h + self.corner_stroke / 2


def _poly(points: list[tuple[float, float]], style: str) -> etree.Element:
    return etree.Element(
        "polygon",
        points=" ".join(f"{x},{y}" for x, y in points),
        style=style,
    )


def add_corner_marks(root: etree.Element, geo: TileGeometry) -> None:
    style = f"fill:none;stroke:black;stroke-width:{geo.corner_stroke}"
    tri = geo.corner_tri
    l, r, t, b = geo.content_left, geo.content_right, geo.content_top, geo.content_bottom

    root.append(_poly([(l, t), (l - tri, t), (l, t - tri)], style))
    root.append(_poly([(r, t), (r + tri, t), (r, t - tri)], style))
    root.append(_poly([(l, b), (l - tri, b), (l, b + tri)], style))
    root.append(_poly([(r, b), (r + tri, b), (r, b + tri)], style))


def add_border(root: etree.Element, geo: TileGeometry) -> None:
    style = (
        f"fill:none;stroke:#E0E0E0;stroke-width:{geo.border_stroke};"
        "stroke-dasharray:0.2,0.5;stroke-dashoffset:0"
    )
    l, r, t, b = geo.content_left, geo.content_right, geo.content_top, geo.content_bottom
    root.append(_poly([(l, t), (r, t), (r, b), (l, b), (l, t)], style))


def add_label(root: etree.Element, geo: TileGeometry, label: str) -> None:
    font_size = geo.corner_tri
    x = geo.content_left
    y = geo.content_bottom + font_size
    root.append(etree.Element(
        "text",
        x=str(x),
        y=str(y),
        style=f"font-size:{font_size};fill:#666666;font-family:'Ubuntu Mono';",
    ))
    root[-1].text = label


def make_tile(tree, x: float, y: float, clip_w: float, clip_h: float,
              tile_id: int, units_per_inch: float, config: ProcessConfig) -> bytes:
    geo = TileGeometry.from_config(config, clip_w, clip_h, units_per_inch)

    root_copy = copy.deepcopy(tree.getroot())

    # Preserve existing <defs>, append clip into them
    defs = root_copy.find("defs")
    if defs is None:
        defs = etree.SubElement(root_copy, "defs")

    clip_id = f"clip_{tile_id}"
    clip = etree.SubElement(defs, "clipPath", id=clip_id)
    etree.SubElement(clip, "rect", x=str(x), y=str(y), width=str(clip_w), height=str(clip_h))

    offset_x = x - geo.origin_x
    offset_y = y - geo.origin_y

    g = etree.Element("g", attrib={
        "clip-path": f"url(#{clip_id})",
        "transform": f"translate({-offset_x}, {-offset_y})",
    })
    for child in list(root_copy):
        if child.tag != "defs":
            root_copy.remove(child)
            g.append(child)
    root_copy.append(g)

    root_copy.set("viewBox", f"0 0 {geo.page_w} {geo.page_h}")
    root_copy.set("width", f"{config.page_width_in}in")
    root_copy.set("height", f"{config.page_height_in}in")

    add_corner_marks(root_copy, geo)
    add_border(root_copy, geo)
    # add_label(root_copy, geo, f"Tile {tile_id}")

    svg_bytes = io.BytesIO()
    etree.ElementTree(root_copy).write(svg_bytes)
    return cairosvg.svg2pdf(bytestring=svg_bytes.getvalue())