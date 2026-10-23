Open file handle leak in main(): open(config.input_file, "rb") is never closed. The PDF path also leaks: open(config.input_file, "rb").read() creates an anonymous handle. Both should use with blocks.

Design Issues
defs elements are removed and re-added unconditionally in make_tile() — existing <defs> (e.g. gradients, symbols, filters used by the SVG content) are stripped before the clipPath is added. This will break SVGs that rely on definitions. The correct approach is to append to existing <defs> or create one only if absent.

Minor / Polish
pymupdf is not in pyproject.toml dependencies — pdf.py imports pymupdf, but it's absent from the declared dependencies. Anyone installing from PyPI will get an ImportError on PDF input.
pdf2image is in pyproject.toml as a hard dependency, but it's only used in the test suite. It should be in an optional [project.optional-dependencies] group (e.g. [test]) rather than required for all users.
