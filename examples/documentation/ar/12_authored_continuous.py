from asmagic import ARDataSubscriber

# Create subscriber with your iPhone's IP address
sub = ARDataSubscriber("192.168.1.100")

try:
    # Continuous data streaming
    while True:
        data = sub.receive()
        # All sensor data in one frame
        print(f"Timestamp: {data.timestamp}")
        print(f"Velocity: {data.velocity}")
        print(f"Local Pose: {data.local_pose}")
        print(f"Global Pose: {data.global_pose}")
        print(f"Camera Intrinsics: {data.camera_intrinsics}")

        # Access image data
        if data.has_color_image:
            # Color: bytes(jpeg format) or array
            color_bytes = data.color_bytes
            color_array = data.color_array  # or shortcut: data.color
            print(f"Color: {len(color_bytes)} bytes, array shape: {color_array.shape}")

        if data.has_depth_image:
            # Depth: Numpy array
            depth = data.depth
            print(f"Depth: {depth.shape}")

        # Additional fields; all original properties above remain unchanged.
        print(f"Frame ID: {data.frame_id}")
        print(f"Capture Timestamp: {data.source_timestamp}")
        print(f"RGB Size: {data.rgb_width}, {data.rgb_height}")
        print(f"RGB Codec: {data.rgb_codec_name}")
        print(f"Depth Size: {data.depth_width}, {data.depth_height}")
        print(f"Depth Confidence: {data.depth_confidence_array}")
        print(f"Depth Scale (m/unit): {data.depth_meters_per_unit}")

        # Display rotation only. Upright depth still uses raw uint16 units.
        print(f"Upright RGB: {data.color_upright}")
        print(f"Upright depth: {data.depth_upright}")
        print(f"Image Rotation (clockwise quarter turns): {data.image_rotation_quarter_turns_clockwise}")

        # Added matrix properties; the original pose/intrinsics arrays stay unchanged.
        print(f"Local Pose Matrix: {data.local_pose_matrix}")
        print(f"Global Pose Matrix: {data.global_pose_matrix}")
        print(f"Camera Intrinsics Matrix: {data.camera_intrinsics_matrix}")
        print(f"Session: {data.session_identifier}")
        print(f"Shared World: {data.shared_world_identifier}")
        print(f"Global Pose Is Shared: {data.global_pose_is_shared}")

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    sub.close()
