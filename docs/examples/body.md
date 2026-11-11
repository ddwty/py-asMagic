# Body Tracking Receiving Examples

Read complete ARKit or MediaPipe body data through the same people, named-joint and array API. See [the illustrated body guide](../body-tracking.md) for coordinates, identity and exact formats.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Read every person and all native joints

Select the App recognition model. Receive once, then read all people and their complete skeletons.

Source: [body/01_all_joints.py](../../examples/documentation/body/01_all_joints.py)

Run from the SDK project directory:

```bash
python examples/documentation/body/01_all_joints.py
```

```python
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
```

## Example 2: Read shoulders, elbows, wrists, hips, knees and ankles

Read twelve named joints on both sides of each person. Print body/world positions, rotations and quality; unavailable data is None.

Source: [body/02_named_joints.py](../../examples/documentation/body/02_named_joints.py)

Run from the SDK project directory:

```bash
python examples/documentation/body/02_named_joints.py
```

```python
from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Match the App setting: "mediapipe" or "arkit".


def print_person_joints(person):
    print(f"\nPerson {person.label} (ID: {person.id})")
    # Read both sides of the upper body and legs by their anatomical names.
    named_joints = [
        ("Left shoulder", person.joints.left_shoulder),
        ("Right shoulder", person.joints.right_shoulder),
        ("Left elbow", person.joints.left_elbow),
        ("Right elbow", person.joints.right_elbow),
        ("Left wrist", person.joints.left_wrist),
        ("Right wrist", person.joints.right_wrist),
        ("Left hip", person.joints.left_hip),
        ("Right hip", person.joints.right_hip),
        ("Left knee", person.joints.left_knee),
        ("Right knee", person.joints.right_knee),
        ("Left ankle", person.joints.left_ankle),
        ("Right ankle", person.joints.right_ankle),
    ]
    for location, body_joint in named_joints:
        if body_joint is None:
            print(f"  {location}: joint unavailable")
            continue
        print(f"  {location}: body [x, y, z] (m)={body_joint.position}")
        print(f"  {location}: world [x, y, z] (m)={body_joint.world_position}")
        print(f"  {location}: rotation [qx, qy, qz, qw]={body_joint.rotation}")
        print(f"  {location}: usable={body_joint.usable}")


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    try:
        while True:
            frame = sub.receive()
            print("\nPeople:", frame.person_count)
            if not frame.people:
                print("No person detected in this frame")
            for person in frame.people:
                print_person_joints(person)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 3: Read skeleton arrays and compare body/world positions

Print all twelve common rows with names, positions, rotations and availability masks. Use the default layout to retain all 33 MediaPipe or 91 ARKit joints.

Source: [body/03_coordinate_spaces.py](../../examples/documentation/body/03_coordinate_spaces.py)

Run from the SDK project directory:

```bash
python examples/documentation/body/03_coordinate_spaces.py
```

```python
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
```

## Example 4: Display all people in separate skeleton panels

SHOW_SKELETON selects plotting. Each local body has its own origin and panel; the receiver preserves every native node.

Source: [body/04_optional_skeleton.py](../../examples/documentation/body/04_optional_skeleton.py)

Run from the SDK project directory:

```bash
python examples/documentation/body/04_optional_skeleton.py
```

```python
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
```

## Example 5: Keep one person by ID across frames

Choose an initial track once. Look it up by ID; tracking loss does not substitute another person.

Source: [body/05_person_id.py](../../examples/documentation/body/05_person_id.py)

Run from the SDK project directory:

```bash
python examples/documentation/body/05_person_id.py
```

```python
from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"
MODEL = "mediapipe"  # This example uses MediaPipe multi-person output.


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    target_id = None
    target_session = None
    try:
        while True:
            frame = sub.receive()
            if target_id is None and frame.people:
                # Choose an initial track once. Keep its ID after tracking loss.
                target_id = frame.people[0].id
                target_session = frame.session_id
                print("Chosen person:", target_id)
            if target_id is None:
                continue
            if frame.session_id != target_session:
                print("Session changed. Choose a new person explicitly.")
                continue
            person = frame.person(target_id)
            if person is None:
                print("Chosen person is absent:", target_id)
                continue
            print("Person:", person.id, "Identity ambiguous:", person.identity_ambiguous)
            skeleton = person.skeleton()
            print("All joint names:", skeleton.names)
            print("Body positions (m):", skeleton.positions)
            print("Position available:", skeleton.valid)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 6: Read all raw-image landmarks and pixels

MediaPipe supplies 33 image coordinates per person. Pixel conversion uses the raw image dimensions.

Source: [body/06_image_landmarks.py](../../examples/documentation/body/06_image_landmarks.py)

Run from the SDK project directory:

```bash
python examples/documentation/body/06_image_landmarks.py
```

```python
import numpy as np
from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
MODEL = "mediapipe"  # Image landmarks are available with MediaPipe.


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    try:
        while True:
            frame = sub.receive()
            width, height = frame.image_width, frame.image_height
            print("\nImage size (width, height):", (width, height))
            if not frame.people:
                print("No person detected in this frame")
                continue
            for person in frame.people:
                image = person.skeleton(space="image")
                print(f"\nPerson {person.label} (ID: {person.id})")
                print("All 33 landmark names:", image.names)
                print("Normalized image positions [x, y]:\n", image.positions)
                print("Position available:", image.valid)
                if width is not None and height is not None and width > 0 and height > 0:
                    pixels = image.positions * np.array([width, height])
                    print("Pixel positions for available landmarks:\n", pixels[image.valid])
                else:
                    print("Image size unavailable; skip pixel conversion")
                print("Visibility:", image.visibility)
                print("Presence:", image.presence)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```
