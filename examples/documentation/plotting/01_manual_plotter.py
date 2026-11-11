from asmagic import BodyTrackingDataSubscriber, TrackingPlotter

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".
SHOW_SKELETON = True


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while viewer is None or viewer.is_open:
            frame = sub.receive(timeout=50 if viewer is not None else 1000)
            if frame is None:
                if viewer is not None:
                    viewer.idle()
                continue
            if viewer is not None:
                viewer.update(frame)
            print("Time:", frame.timestamp)
            for person in frame.people:
                print("Person:", person.id, "Positions (m):", person.skeleton().positions)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
