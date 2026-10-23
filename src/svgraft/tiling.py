import math

# This is to prevent floating point precision errors from using extra pages when the clip size should divide
# perfectly into the clip region
EPSILON = 1e-9

def compute_tiles(total_w, total_h, clip_w, clip_h):
    cols = math.ceil(total_w / clip_w - EPSILON)
    rows = math.ceil(total_h / clip_h - EPSILON)

    return cols, rows