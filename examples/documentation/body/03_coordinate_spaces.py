from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    try:
        while True:
            frame = sub.receive()
            if not frame.people:
                print("No person detected in this frame")
                continue
            for person in frame.people:
                # Omit layout="common" to read all 33 or 91 model-specific rows.
                body = person.skeleton(space="body", layout="common")
                world = person.skeleton(space="world", layout="common")
                print(f"\nPerson {person.label} (ID: {person.id})")
                print("Joint names:", body.names)
                print("Body positions [x, y, z] (m):\n", body.positions)
                print("Position available:", body.valid)
                print("Usable positions:", body.usable)
                print("Rotations [qx, qy, qz, qw]:\n", body.rotations)
                print("Rotation available:", body.rotation_valid)
                print("Available body positions only:\n", body.positions[body.valid])

                # A row identifies the same joint in the body and world arrays.
                for row, name in enumerate(body.names):
                    body_position = body.positions[row] if body.valid[row] else None
                    world_position = world.positions[row] if world.valid[row] else None
                    print(f"Row {row} ({name}): body={body_position}, "
                          f"world={world_position}")
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
