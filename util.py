import bpy
import bmesh
from mathutils import Vector
import numpy as np

def lin_log(x, threshold=20):
    """
    linear mapping + logarithmic mapping.
    :param x: float or ndarray
        the input linear value in range 0-1
    :param threshold: float threshold 0-255
        the threshold for transition from linear to log mapping
    Returns: the log value
    """
    # converting x into np.float64.
    if x.dtype is not np.float64:  # note float64 to get rounding to work
        x = x.astype(np.float64)

    x = np.maximum(x * 255.0, 1.0e-8)
    f = (1.0 / threshold) * np.log(threshold)
    y = np.where(x <= threshold, x * f, np.log(x))

    rounding = 1e8
    y = np.round(y * rounding) / rounding

    return y.astype(x.dtype)

class CamPoses(object):
    def __init__(self, cam):
        self.pos = Vector(cam.location)
        self.lf = cam.lightfield
        self.grid = (self.lf.num_rows, self.lf.num_cols)
        dir = cam.matrix_world.to_3x3().normalized()
        self.dx = dir @ Vector((-1., 0., 0.)) * self.lf.base_x
        self.dy = dir @ Vector((0., 1., 0.)) * self.lf.base_y

    def __len__(self):
        return self.grid[0] * self.grid[1]

    def __getitem__(self, index):
        S, T = self.grid
        if isinstance(index, int):
            s, t = self.idx2pos(index)
        else:
            s, t = index
        dx = self.dx * (2*t/(T-1)-1) if T > 1 else Vector((0,0,0))
        dy = self.dy * (2*s/(S-1)-1) if S > 1 else Vector((0,0,0))
        return self.pos + dx + dy

    def bound(self, s, t):
        S, T = self.grid
        return (max(0, min(s, S-1)), max(0, min(t, T-1)))

    def pos2idx(self, s, t):
        T = self.grid[1]
        return s*T+t

    def idx2pos(self, index):
        T = self.grid[1]
        return index // T, index % T
    
    def get_shiftx(self, index):
        S, T = self.grid
        if isinstance(index, int):
            s, t = self.idx2pos(index)
        else:
            s, t = index
        return self.lf.base_x * (2*t/(T-1)-1) if T > 1 else 0
    
    def get_shifty(self, index):
        S, T = self.grid
        if isinstance(index, int):
            s, t = self.idx2pos(index)
        else:
            s, t = index
        return self.lf.base_y * (2*s/(S-1)-1) if S > 1 else 0