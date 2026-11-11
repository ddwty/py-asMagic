# Skeleton Plotting API Examples

Display or save received tracking frames.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Receive frames with an optional TrackingPlotter

Display the received frame. Close the window or press Ctrl-C to finish.

Source: [plotting/01_manual_plotter.py](../../examples/documentation/plotting/01_manual_plotter.py)

Run from the SDK project directory:

```bash
python examples/documentation/plotting/01_manual_plotter.py
```

```python
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
```

## Example 2: frame.plot() or plot_tracking() with a shared window

Display the received frame. Close the window or press Ctrl-C to finish.

Source: [plotting/02_frame_plot.py](../../examples/documentation/plotting/02_frame_plot.py)

Run from the SDK project directory:

```bash
python examples/documentation/plotting/02_frame_plot.py
```

```python
from asmagic import TrackingPlotter
from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
SHOW_SKELETON = True


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter() if SHOW_SKELETON else None
    try:
        while True:
            frame = sub.receive()
            if viewer is not None:
                if not viewer.is_open:
                    break
                viewer.update(frame)
            print("Time:", frame.timestamp)
            print("Hand count:", frame.hand_count)
    except KeyboardInterrupt:
        pass
    finally:
        if viewer is not None:
            viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 3: Plot a single Hand object

Display the received frame. Close the window or press Ctrl-C to finish.

Source: [plotting/03_single_hand.py](../../examples/documentation/plotting/03_single_hand.py)

Run from the SDK project directory:

```bash
python examples/documentation/plotting/03_single_hand.py
```

```python
from asmagic import TrackingPlotter
from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    viewer = TrackingPlotter()
    try:
        while True:
            frame = sub.receive()
            hand = frame.left_hand
            if hand is not None:
                viewer.update(hand)
                print("Time:", frame.timestamp)
                print("Left hand points:", hand.as_arrays().points)
            else:
                viewer.idle()
            if not viewer.is_open:
                break
    except KeyboardInterrupt:
        pass
    finally:
        viewer.close()
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 4: Save a real received skeleton without a window

Save a received skeleton to PNG without opening a window.

Source: [plotting/04_save_without_window.py](../../examples/documentation/plotting/04_save_without_window.py)

Run from the SDK project directory:

```bash
python examples/documentation/plotting/04_save_without_window.py
```

```python
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
```
