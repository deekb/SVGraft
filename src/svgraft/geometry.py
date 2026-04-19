from .config import MM_PER_INCH

def mm_to_units(mm, units_per_inch):
    return (mm / MM_PER_INCH) * units_per_inch