from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def print_hand_arrays(side, hand):
    print(f"\n{side} hand:")
    if hand is None:
        print("Not detected")
        return

    joints = hand.as_arrays()

    # The same row refers to the same joint in all four fields.
    print("Joint names:", joints.names)
    print("Normalized positions [x, y]:\n", joints.points)
    print("Joint confidences:", joints.confidences)
    print("Joint present:", joints.valid)

    # Print every row: wrist, thumb, index, middle, ring and little finger.
    for row, name in enumerate(joints.names):
        if joints.valid[row]:
            print(f"Row {row} ({name}): [x, y]={joints.points[row]}, "
                  f"confidence={joints.confidences[row]}")
        else:
            print(f"Row {row} ({name}): not detected")

    # Boolean indexing selects only the joints that are present.
    print("Present joint positions:\n", joints.points[joints.valid])


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("\nTime:", frame.timestamp)
            print_hand_arrays("Left", frame.left)
            print_hand_arrays("Right", frame.right)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
