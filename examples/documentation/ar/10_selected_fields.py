from asmagic import ARDataSubscriber
import numpy as np

sub = ARDataSubscriber("192.168.1.100")

for data in sub:
    K = np.array(data.camera_intrinsics).reshape(3, 3, order='F')
    scale_x = 640 / 1920  # = 1/3
    scale_y = 480 / 1440  # = 1/3

    K[0, 0] *= scale_x  # fx
    K[1, 1] *= scale_y  # fy
    K[0, 2] *= scale_x  # cx
    K[1, 2] *= scale_y  # cy

    print(f"Scaled intrinsics:\n{K}")
