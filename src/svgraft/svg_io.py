import re
from .config import MM_PER_INCH
from .debug import debug

def parse_length(val):
    match = re.match(r"([0-9.]+)([a-z%]*)", val)
    if not match:
        return float(val), "px"
    value, unit = match.groups()
    return float(value), unit or "px"


def get_units_per_inch(root):
    view_box = root.get("viewBox")
    if not view_box:
        raise ValueError("SVG must have a viewBox")

    _, _, vb_w, _ = map(float, view_box.split())

    width_val, width_unit = parse_length(root.get("width", "0"))

    debug("SVG unit parse", {
        "viewBox": view_box,
        "width": root.get("width"),
        "width_unit": width_unit,
        "vb_w": vb_w
    })

    if width_unit == "in":
        return vb_w / width_val
    elif width_unit == "mm":
        return vb_w / (width_val / MM_PER_INCH)
    else:
        raise ValueError("Width must be defined in inches or mm")