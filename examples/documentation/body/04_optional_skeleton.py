from asmagic import BodyTrackingDataSubscriber, TrackingPlotter

IPHONE_IP = "192.168.1.100"
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".
SHOW_SKELETON = True


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    plotter = None
    try:
        plotter = TrackingPlotter(space="body", min_confidence=0.5) if SHOW_SKELETON else None
        while plotter is None or plotter.is_open:
            frame = sub.receive(timeout=50 if plotter is not None else 1000)
            if frame is None:
                if plotter is not None:
                    plotter.idle()
                continue
            print("People:", frame.person_count, "IDs:", [person.id for person in frame.people])
            if plotter is not None:
                plotter.update(frame)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()
        if plotter is not None:
            plotter.close()


if __name__ == "__main__":
    main()
