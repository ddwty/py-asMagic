from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from asmagic import BodyTrackingDataSubscriber, TrackingPlotter

IPHONE_IP = "192.168.1.100"
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".
OUTPUT = Path("reports/manual-body.png")


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    viewer = TrackingPlotter(labels=True)
    try:
        while True:
            frame = sub.receive()
            if not any(person.skeleton().valid.any() for person in frame.people):
                print('Waiting for body positions')
                continue
            viewer.update(frame, force=True)
            viewer.figure.suptitle('Body tracking snapshot')
            viewer.axes[0].set_title('Session: ' + frame.session_id)
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            viewer.save(OUTPUT, dpi=150, bbox_inches='tight')
            print('Saved:', OUTPUT.resolve())
            break
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()
        viewer.close()


if __name__ == "__main__":
    main()
