# SVGraft Roadmap

## Scale Control

Currently SVGraft tiles an SVG at its native size. The goal is to let users control the output scale before tiling, with margins factored into every calculation.

### Percentage scaling
Scale the SVG up or down by a percentage of its original size before tiling.

```bash
svgraft poster.svg --scale 150%
```

### Target page count
Specify how many pages wide and/or tall the final tiled output should span. SVGraft back-calculates the required scale to hit that grid exactly, accounting for per-page margins eating into usable area.

```bash
svgraft poster.svg --pages-wide 3
svgraft poster.svg --pages-wide 3 --pages-tall 2
```

### Target physical dimensions
Specify the desired real-world width or height of the final assembled poster (e.g. "I want this 4 feet wide"). SVGraft derives the scale factor from the target dimension and the SVG's native physical size, then tiles accordingly.

```bash
svgraft poster.svg --output-width 48in
svgraft poster.svg --output-height 1200mm
```

All three modes must account for margins — the usable area per page (page size minus margins) is what determines how the scaled content maps onto tiles, not the raw page dimensions.

---

## Broader Input Format Support

### PDF input
Accept PDF files directly as input. The most viable path is converting each PDF page to an SVG (via a tool such as `pdf2svg` or `cairo`) and running it through the existing pipeline. Multi-page PDFs could either tile each page separately or be treated as a single document.

```bash
svgraft document.pdf --scale 200%
```

### Other vector formats
Formats such as `.ai`, `.eps`, and `.wmf` may be convertible to SVG via existing libraries and could follow the same path as PDF once a reliable conversion step is established.

### Raster input
Accept raster images (`.png`, `.jpg`, `.tiff`, etc.) as input. The conversion approach would embed the raster inside an SVG wrapper at the correct physical dimensions, then tile normally. Quality is bounded by the source resolution, so a DPI warning should be surfaced when the source image is too low-res for the requested output size (<360 DPI).

```bash
svgraft photo.png --output-width 36in
```

A shared conversion layer (e.g. `svgraft.converters`) could handle all non-SVG input types and normalize them to SVG before handing off to the existing pipeline, keeping the core tiling logic format-agnostic.

---

## Open Questions

- **PDF multi-page input:** tile all pages into one output PDF, or produce one output PDF per input page?
- **Raster DPI threshold:** what minimum source DPI should trigger a warning, and should the user be able to suppress it?
- **Scale conflict resolution:** if the user supplies both `--pages-wide` and `--output-width`, which wins — or should it be an error?
- **Orientation optimisation with scaling:** when scaling to a target page count, should orientation optimisation be disabled (since the user has expressed an explicit layout intent)?