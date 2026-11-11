"""Explicit coordinate conversions; never apply display mirroring to received data."""
from typing import Optional
import numpy as np


def pose_matrix(pose) -> Optional[np.ndarray]:
    values = np.asarray(pose, dtype=np.float32)
    if values.size == 16:
        # Preserve the 0.1.x matrix helper's legacy row-major interpretation.
        return values.reshape(4, 4)
    if values.size != 7:
        return None
    x, y, z, w = values[3:]
    norm = float(x*x + y*y + z*z + w*w)
    if norm <= 1e-12 or not np.isfinite(norm):
        raise ValueError("Pose quaternion must be finite and non-zero")
    s = 2.0 / norm
    matrix = np.eye(4, dtype=np.float32)
    matrix[:3, :3] = [
        [1-s*(y*y+z*z), s*(x*y-z*w), s*(x*z+y*w)],
        [s*(x*y+z*w), 1-s*(x*x+z*z), s*(y*z-x*w)],
        [s*(x*z-y*w), s*(y*z+x*w), 1-s*(x*x+y*y)],
    ]
    matrix[:3, 3] = values[:3]
    return matrix
