# Runnable examples

Each script imports the installed SDK directly and can be run independently.
Edit the IP address and display settings at the top, then run it from the repository root.
For Watch, configure the device to send to your computer's address.

[Setup and guides](../../docs/examples/index.md) · [Data format and API](../../docs/examples/api-reference.md)

| File | Example |
|---|---|
| [camera/00_receive_image_data.py](camera/00_receive_image_data.py) | Read camera image data |
| [camera/01_preview.py](camera/01_preview.py) | Live video preview |
| [camera/02_rgb_arrays.py](camera/02_rgb_arrays.py) | Read RGB arrays and timestamps |
| [camera/03_save_image.py](camera/03_save_image.py) | Save one image |
| [ar/01_continuous.py](ar/01_continuous.py) | Continuous AR data reading |
| [ar/03_display_images.py](ar/03_display_images.py) | Optionally display color and depth |
| [ar/04_image_arrays.py](ar/04_image_arrays.py) | Process RGB, depth and confidence arrays |
| [ar/05_pose_matrices.py](ar/05_pose_matrices.py) | Positions, quaternions and matrices |
| [ar/07_metadata.py](ar/07_metadata.py) | Frame and session information |
| [ar/08_frame_fields.py](ar/08_frame_fields.py) | Read image and pose fields |
| [imu/01_all_sensors.py](imu/01_all_sensors.py) | Read all available IMU sensors |
| [joystick/03_named_controls.py](joystick/03_named_controls.py) | Read named controller controls |
| [joystick/02_full_controller.py](joystick/02_full_controller.py) | All named controller data |
| [joystick/01_sticks_and_buttons.py](joystick/01_sticks_and_buttons.py) | Old API: sticks and numbered buttons |
| [airpods/01_rotation.py](airpods/01_rotation.py) | AirPods rotation quaternion |
| [body/01_all_joints.py](body/01_all_joints.py) | Read every person and all native joints |
| [body/02_named_joints.py](body/02_named_joints.py) | Read shoulders, elbows, wrists, hips, knees and ankles |
| [body/03_coordinate_spaces.py](body/03_coordinate_spaces.py) | Read skeleton arrays and compare body/world positions |
| [body/04_optional_skeleton.py](body/04_optional_skeleton.py) | Display all people in separate skeleton panels |
| [upper_body/01_relative_joints.py](upper_body/01_relative_joints.py) | Upper-body joints, angles and detection metadata |
| [upper_body/02_optional_skeleton.py](upper_body/02_optional_skeleton.py) | Enable or disable the upper-body skeleton |
| [hand/01_both_hands.py](hand/01_both_hands.py) | Read all joints from both hands |
| [hand/02_named_joints_and_pixels.py](hand/02_named_joints_and_pixels.py) | Wrist and all five fingertips in image coordinates |
| [hand/04_joint_arrays.py](hand/04_joint_arrays.py) | Read all hand joints as arrays |
| [hand/03_optional_skeleton.py](hand/03_optional_skeleton.py) | Enable or disable both hand skeletons |
| [face/01_face.py](face/01_face.py) | Face observations and frame metadata |
| [face/02_blendshapes.py](face/02_blendshapes.py) | All available facial movement coefficients |
| [face/03_metric_mesh.py](face/03_metric_mesh.py) | Metric face vertices and triangle topology |
| [face/05_optional_plot.py](face/05_optional_plot.py) | Enable or disable the face plot |
| [claw/01_first_gripper.py](claw/01_first_gripper.py) | First gripper command and optional motor state |
| [claw/02_second_gripper.py](claw/02_second_gripper.py) | Second gripper on a separate port |
| [watch/01_batches.py](watch/01_batches.py) | Receive Watch HTTP batches continuously |
| [watch/02_individual_samples.py](watch/02_individual_samples.py) | Flatten batches into individual Watch samples |
| [watch/03_receive_methods.py](watch/03_receive_methods.py) | Receive Watch samples |
| [watch/04_payload_format_and_decode.py](watch/04_payload_format_and_decode.py) | Select Watch payload format and decode a batch |
| [common/07_receive_loop.py](common/07_receive_loop.py) | Receive one frame and read its fields |
| [common/01_options_timeout_and_cleanup.py](common/01_options_timeout_and_cleanup.py) | Receiving with a timeout and status |
| [common/02_stream_callback.py](common/02_stream_callback.py) | Process a received frame |
| [common/03_named_stream_factory.py](common/03_named_stream_factory.py) | Discover streams and subscribe by name |
| [common/04_raw_protobuf.py](common/04_raw_protobuf.py) | Read raw Protobuf from a received frame |
| [common/05_save_protobuf_frame.py](common/05_save_protobuf_frame.py) | Save one received frame for offline decoding |
| [common/06_decode_saved_frame.py](common/06_decode_saved_frame.py) | Decode a saved typed frame without a socket |
| [legacy/01_magiclaw_combined.py](legacy/01_magiclaw_combined.py) | Legacy combined MagiClaw publisher |
| [legacy/02_watch_zmq.py](legacy/02_watch_zmq.py) | Legacy Watch ZeroMQ publisher |
| [plotting/01_manual_plotter.py](plotting/01_manual_plotter.py) | Receive frames with an optional TrackingPlotter |
| [plotting/02_frame_plot.py](plotting/02_frame_plot.py) | frame.plot() or plot_tracking() with a shared window |
| [plotting/03_single_hand.py](plotting/03_single_hand.py) | Plot a single Hand object |
| [plotting/04_save_without_window.py](plotting/04_save_without_window.py) | Save a real received skeleton without a window |
| [face/06_face_and_hands.py](face/06_face_and_hands.py) | Receive hands from Face and Hand Tracking |
| [face/07_field_types.py](face/07_field_types.py) | Inspect every face field and its Python type |
| [face/08_regions_and_box.py](face/08_regions_and_box.py) | Read landmark regions and raw bounding-box pixels |
| [ar/09_intrinsics.py](ar/09_intrinsics.py) | Scale intrinsics using verified reference dimensions |
| [body/05_person_id.py](body/05_person_id.py) | Keep one person by ID across frames |
| [body/06_image_landmarks.py](body/06_image_landmarks.py) | Read all raw-image landmarks and pixels |
| [ar/10_selected_fields.py](ar/10_selected_fields.py) | Original camera intrinsics scaling example |
| [ar/11_quick_start.py](ar/11_quick_start.py) | Quick Start AR receiving example |
| [ar/12_authored_continuous.py](ar/12_authored_continuous.py) | Authored AR continuous receiving example |
| [imu/02_quick_start.py](imu/02_quick_start.py) | Original Quick Start IMU receiving example |

Set `SHOW_SKELETON = True/False` to toggle tracking plots. `frame.show_images()` displays color and depth by default; pass `show_depth=False` or `show_color=False` to disable either view.
Run `python tools/sync_documentation_examples.py --check` to check that documentation and source code match.
