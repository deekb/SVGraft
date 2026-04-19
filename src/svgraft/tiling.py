import math

def compute_tiles(total_w, total_h, clip_w, clip_h):
    cols = math.ceil(total_w / clip_w)
    rows = math.ceil(total_h / clip_h)

    return cols, rows