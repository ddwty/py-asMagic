from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    try:
        while True:
            frame = sub.receive()
            print("\nSource time (Unix seconds):", frame.timestamp)
            print("Model:", frame.model.value, "People:", frame.person_count)
            if not frame.people:
                print("No person detected in this frame")
                continue

            # Each iteration reads one person's complete skeleton.
            for person in frame.people:
                print(f"\nPerson {person.label} (ID: {person.id})")
                skeleton = person.skeleton()
                for row, name in enumerate(skeleton.names):
                    if skeleton.valid[row]:
                        print(f"  {name}: [x, y, z] (m)={skeleton.positions[row]}, "
                              f"usable={skeleton.usable[row]}")
                    else:
                        print(f"  {name}: body position unavailable")
                    if skeleton.rotation_valid[row]:
                        print(f"  {name}: rotation [qx, qy, qz, qw]="
                              f"{skeleton.rotations[row]}")
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
