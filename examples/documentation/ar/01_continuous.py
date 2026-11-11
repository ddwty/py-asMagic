from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Frame ID:", frame.frame_id)
            print("Capture time:", frame.source_timestamp)

            print("RGB:", frame.color_array)
            print("RGB size:", frame.rgb_width, frame.rgb_height)
            print("Depth (raw):", frame.depth)
            print("Depth size:", frame.depth_width, frame.depth_height)
            print("Depth confidence:", frame.depth_confidence_array)
            print("Depth scale (m/unit):", frame.depth_meters_per_unit)

            print("Velocity (m/s):", frame.velocity)
            print("Local pose:", frame.local_pose)
            print("Global pose:", frame.global_pose)
            print("Local transform:", frame.local_pose_matrix)
            print("Global transform:", frame.global_pose_matrix)
            print("Intrinsics:", frame.camera_intrinsics)
            print("Intrinsics matrix:", frame.camera_intrinsics_matrix)

            print("Session:", frame.session_identifier)
            print("Shared world:", frame.shared_world_identifier)
            print("Global pose is shared:", frame.global_pose_is_shared)
            print("Has RGB / depth / pose:", frame.has_color_image, frame.has_depth_image, frame.has_pose)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
