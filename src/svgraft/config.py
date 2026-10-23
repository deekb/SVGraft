MM_PER_INCH = 25.4
MM_PER_METER = 1000.0

DEFAULTS = {
    "page_width_in":8.5,
    "page_height_in":11,
    "total_width_in":None,
    "total_height_in":None,
    "pages_tall":None,
    "pages_wide":None,
    "scale_factor":None,
    "optimize_tile_orientation":True,
    "margin_mm":7.0,
    "corner_triangle_size_mm":2.0,
    "corner_triangle_stroke":0.1,
    "border_stroke_mm":0.1,
    "input_file":"./input.svg",
    "output_file":"./output_merged.pdf"
}

class ProcessConfig:
    page_width_in: float
    page_height_in: float
    total_width_in: float
    total_height_in: float
    pages_tall: int
    pages_wide: int
    scale_factor: float
    optimize_tile_orientation: bool
    margin_mm: float
    corner_triangle_size_mm: float
    corner_triangle_stroke: float
    border_stroke_mm: float
    input_file: str
    output_file: str

    def __init__(self,
                 page_width_in=None,
                 page_height_in=None,
                 total_width_in=None,
                 total_height_in=None,
                 pages_tall=None,
                 pages_wide=None,
                 scale_factor=None,
                 optimize_tile_orientation=None,
                 margin_mm=None,
                 corner_triangle_size_mm=None,
                 corner_triangle_stroke=None,
                 border_stroke_mm=None,
                 input_file=None,
                 output_file=None):

        for name, value in locals().items():
            if name == "self":
                continue
            if value is not None:
                setattr(self, name, value)
            else:
                setattr(self, name, DEFAULTS[name])

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
