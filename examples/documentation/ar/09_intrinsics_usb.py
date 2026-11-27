from asmagic import ARDataSubscriber

with ARDataSubscriber("usb") as sub:
    for data in sub:
        K_rgb = data.camera_intrinsics_matrix
        if K_rgb is None or data.rgb_width <= 0 or data.rgb_height <= 0:
            continue
        print("RGB intrinsics:", K_rgb)
        if data.has_depth_image:
            K_depth = K_rgb.copy()
            K_depth[0, :] *= data.depth_width / data.rgb_width
            K_depth[1, :] *= data.depth_height / data.rgb_height
            print("Registered depth intrinsics:", K_depth)
