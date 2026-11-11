from pathlib import Path
from asmagic import ARDataSubscriber

INPUT = Path("reports/manual-ar-frame.bin")


def main():
    if not INPUT.is_file():
        print("First run common/05_save_protobuf_frame.py to create", INPUT)
        return
    frame = ARDataSubscriber.decode(INPUT.read_bytes())
    print("Timestamp:", frame.timestamp)
    print("Local pose:", frame.local_pose)
    print("RGB:", frame.color_array)
    print("Depth:", frame.depth)
    print("Depth size:", frame.depth_width, frame.depth_height)


if __name__ == "__main__":
    main()
