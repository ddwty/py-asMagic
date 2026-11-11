from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if frame.local_pose.size == 7:
                print('Position (m):', frame.local_pose[:3])
                print('Quaternion (x/y/z/w):', frame.local_pose[3:])
            print('Local transform:', frame.local_pose_matrix)
            print('Global transform:', frame.global_pose_matrix)
            print('Camera K:', frame.camera_intrinsics_matrix)
            print('Velocity (m/s):', frame.velocity)
            print('Shared world:', frame.global_pose_is_shared, frame.shared_world_identifier)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
