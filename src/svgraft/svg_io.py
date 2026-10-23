import re
from .config import MM_PER_INCH, MM_PER_METER
from .debug import debug


def parse_length(val):
    """
    Parse an SVG length string into a numeric value and unit.

    Supports values with optional units (e.g., "100", "8.5in", "210mm").
    If no unit is provided, defaults to pixels ("px").

    Args:
        val (str): The length string to parse.

    Returns:
        tuple[float, str]: A tuple containing:
            - The numeric value as a float.
            - The unit as a string (e.g., "px", "in", "mm").

    Raises:
        ValueError: If the value cannot be converted to a float.
    """
    match = re.match(r"([0-9.]+)([a-z%]*)", val)
    if not match:
        return float(val), "px"

    value, unit = match.groups()
    return float(value), unit or "px"

def convert_to_inches(val):
    value, unit = parse_length(val)
    if unit in ["in", "inches", "inch"]:
        return float(value)
    elif unit in ["mm", "millimeters", "millimeter"]:
        return float(value) / MM_PER_INCH
    elif unit in ["m", "meters", "meter"]:
        return float(value) / MM_PER_INCH * MM_PER_METER
    else:
        raise ValueError("Unit must be defined in inches, mm, or m")


def get_units_per_inch(root):
    """
    Compute the number of SVG user units per inch.

    This function derives a conversion factor between the SVG's internal
    coordinate system (defined by the viewBox) and physical units based on
    the declared width of the SVG element.

    Only widths defined in inches ("in") or millimeters ("mm") are supported.
    The function uses the viewBox width and the physical width to determine
    the scaling factor.

    Args:
        root (lxml Element): The root <svg> element.

    Returns:
        float: The number of SVG units per inch.

    Raises:
        ValueError: If the SVG does not have a viewBox or if the width unit
            is not supported.
    """
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