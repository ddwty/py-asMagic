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
