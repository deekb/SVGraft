import unittest
from pathlib import Path
from pdf2image import convert_from_path

from src.svgraft.cli import split_svg

class TestCalculator(unittest.TestCase):
    def test_split(self):
        input_path = Path("tests/data/test_poster.svg")
        self.assertTrue(input_path.is_file(), f"The test could not be completed because it is missing the input file at {input_path} does not exist")
        output_path = Path("./test_poster_spit.pdf")
        output_path.unlink(True)
        split_svg(input_path, page_width_in=8.5, page_height_in=11, margin_mm=5, output_file=output_path, optimize_tile_orientation=True)
        self.assertTrue(output_path.is_file(), "The output file was not created")
        pages = convert_from_path(output_path, dpi=96)

        # Example: Display using PIL
        print(f"Page count: {len(pages)}")
        print("Displaying page 1 previewed at 96DPI")
        pages[0].show()
