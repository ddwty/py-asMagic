from asmagic import FaceDataSubscriber
from asmagic.geometry import pose_matrix
import numpy as np

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if not frame.has_face:
                print('No face in this frame')
                continue
            print('Flat triangle IDs:', frame.triangle_indices)
            vertices = frame.face_vertices
            if vertices is None or frame.tracking_mode != 'true_depth':
                print('Metric face mesh unavailable')
                continue
            row_by_id = {point.index: row for row, point in enumerate(frame.landmarks)}
            triangle_rows = np.array([
                [row_by_id[int(vertex)] for vertex in triangle]
                for triangle in frame.triangles
                if all(int(vertex) in row_by_id for vertex in triangle)
            ], dtype=np.int32).reshape(-1, 3)
            print('Vertices (m):', vertices)
            print('Triangle row indices:', triangle_rows)
            print('Triangle vertex coordinates (M x 3 x 3):', vertices[triangle_rows])
            position = frame.camera_position_meters
            orientation = frame.camera_orientation
            if position is not None and orientation is not None:
                # Face-local -> camera coordinates, in meters; no image mirroring.
                camera_from_face = pose_matrix(np.concatenate([position, orientation]))
                camera_vertices = vertices @ camera_from_face[:3, :3].T + position
                print('Camera-from-face matrix:', camera_from_face)
                print('Camera-relative vertices (m):', camera_vertices)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
