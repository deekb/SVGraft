import copy
import io
import cairosvg
from lxml import etree

from .geometry import mm_to_units
from .config import (DEFAULT_PAGE_WIDTH_IN,
                     DEFAULT_PAGE_HEIGHT_IN,
                     DEFAULT_CORNER_TRIANGLE_MM,
                     DEFAULT_CORNER_STROKE_MM)


def add_corner_marks(root, units_per_inch, page_w, page_h, clip_w, clip_h):
    tri = mm_to_units(DEFAULT_CORNER_TRIANGLE_MM, units_per_inch)
    stroke = mm_to_units(DEFAULT_CORNER_STROKE_MM, units_per_inch)

    def tri_elem(points):
        return etree.Element("polygon", points=" ".join(f"{x},{y}" for x, y in points),
                             style=f"fill:none;stroke:black;stroke-width:{stroke}")

    def border_elem(points):
        "stroke-dasharray:1,12;stroke-dashoffset:0"
        return etree.Element("polygon", points=" ".join(f"{x},{y}" for x, y in points),
                             style=f"fill:none;stroke:#e6e6e6;stroke-width:{stroke};stroke-dasharray:0.2,0.5;stroke-dashoffset:0")

    ox = (page_w - clip_w) / 2
    oy = (page_h - clip_h) / 2

    stroke_offset = stroke / 2

    left, right = ox - stroke_offset, ox + clip_w + stroke_offset
    top, bottom = oy + stroke_offset, oy + clip_h - stroke_offset

    root.append(tri_elem([(left, top), (left - tri, top), (left, top - tri)]))
    root.append(tri_elem([(right, top), (right + tri, top), (right, top - tri)]))
    root.append(tri_elem([(left, bottom), (left - tri, bottom), (left, bottom + tri)]))
    root.append(tri_elem([(right, bottom), (right + tri, bottom), (right, bottom + tri)]))
    root.append(border_elem([(left, top), (right, top), (right, bottom), (left, bottom), (left, top)]))


def make_tile(tree, x, y, clip_w, clip_h, tile_id, units_per_inch, page_width_in=DEFAULT_PAGE_WIDTH_IN,
              page_height_in=DEFAULT_PAGE_HEIGHT_IN):
    # debug("")
    # debug(f"Render tile {tile_id}",
    #       {
    #           "id": tile_id,
    #           "x (mm)": round(x, 4),
    #           "y (mm)": round(y, 4),
    #           "width (mm):": round(clip_w, 4),
    #           "height (mm):": round(clip_h, 4),
    #           "width (in):": round(mm_to_units(clip_w, 1), 4),
    #           "height (in):": round(mm_to_units(clip_h, 1), 4)})

    root = tree.getroot()
    root_copy = copy.deepcopy(root)

    page_w = page_width_in * units_per_inch
    page_h = page_height_in * units_per_inch

    for el in root_copy.findall("defs"):
        root_copy.remove(el)

    defs = etree.SubElement(root_copy, "defs")

    clip_id = f"clip_{tile_id}"
    clip = etree.SubElement(defs, "clipPath", id=clip_id)

    etree.SubElement(clip, "rect", x=str(x), y=str(y), width=str(clip_w), height=str(clip_h))

    offset_x = x - ((page_w - clip_w) / 2)
    offset_y = y - ((page_h - clip_h) / 2)

    g = etree.Element("g",
                      attrib={"clip-path": f"url(#{clip_id})", "transform": f"translate({-offset_x}, {-offset_y})"})

    for child in list(root_copy):
        if child.tag != "defs":
            root_copy.remove(child)
            g.append(child)

    root_copy.append(g)

    root_copy.set("viewBox", f"0 0 {page_w} {page_h}")
    root_copy.set("width", f"{page_width_in}in")
    root_copy.set("height", f"{page_height_in}in")

    add_corner_marks(root_copy, units_per_inch, page_w, page_h, clip_w, clip_h)

    svg_bytes = io.BytesIO()
    etree.ElementTree(root_copy).write(svg_bytes)

    return cairosvg.svg2pdf(bytestring=svg_bytes.getvalue())
