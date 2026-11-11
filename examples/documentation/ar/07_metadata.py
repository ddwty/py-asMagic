from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print('Frame ID:', frame.frame_id)
            print('Timestamps:', frame.timestamp, frame.source_timestamp)
            print('RGB dimensions:', frame.rgb_width, frame.rgb_height)
            print('Depth dimensions:', frame.depth_width, frame.depth_height)
            print('Depth scale (m/unit):', frame.depth_meters_per_unit)
            print('Session:', frame.session_identifier)
            print('Shared world:', frame.shared_world_identifier, frame.global_pose_is_shared)
            print('Has RGB / depth / pose:', frame.has_color_image, frame.has_depth_image, frame.has_pose)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
