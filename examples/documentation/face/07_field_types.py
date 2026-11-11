from dataclasses import fields

import numpy as np
from asmagic import FaceDataSubscriber, FaceFrame

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
FRAME_FIELDS = tuple(item.name for item in fields(FaceFrame)) + (
    'timestamp', 'blendshape_coefficients', 'points', 'triangles', 'face_vertices',
)


def describe(value):
    if isinstance(value, np.ndarray):
        return 'numpy.ndarray, dtype={}, shape={}'.format(value.dtype, value.shape)
    if isinstance(value, (dict, tuple)):
        return '{}; count={}'.format(type(value).__name__, len(value))
    return '{}: {}'.format(type(value).__name__, value)


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive(timeout=1000)
            if frame is None:
                print('No new frame within the timeout')
                continue
            print('Frame type:', type(frame).__name__)
            for name in FRAME_FIELDS:
                value = getattr(frame, name)
                if name == 'protobuf':
                    print(name, type(value).__name__, value.DESCRIPTOR.full_name)
                else:
                    print(name, describe(value))
            if frame.image_location is not None:
                for item in fields(frame.image_location):
                    print('image_location.' + item.name,
                          describe(getattr(frame.image_location, item.name)))
            if frame.landmarks:
                point = frame.landmarks[0]
                for item in fields(point):
                    print('landmarks[0].' + item.name,
                          describe(getattr(point, item.name)))
            if frame.blendshapes:
                name = next(iter(frame.blendshapes))
                print('Blendshape key:', describe(name))
                print('Blendshape value:', describe(frame.blendshapes[name]))
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
