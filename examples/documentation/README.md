# GitBook examples

These files contain the exact Python code shown in the corresponding GitBook chapters, including each Network and USB tab. Files ending in `_usb.py` use USB.

Install this checkout with `python -m pip install -e .`. Run scripts from the SDK directory; edit the connection and model settings at the top when needed. Start the matching output in asMagic first.

For USB, connect a data cable, unlock and trust the computer, and keep asMagic in the foreground. Use `asmagic usb list` to find a device; replace `"usb"` with `"usb:DEVICE_UDID"` when several are attached.

```bash
python examples/documentation/imu/01_all_sensors_usb.py
python examples/documentation/camera/01_preview_usb.py
python examples/documentation/hand/03_optional_skeleton_usb.py
```

Body examples select ARKit or MediaPipe with `MODEL`; match the app setting.

## Chapters and files

| GitBook chapter | Local file | Connection | Type |
|---|---|---|---|
| [Quick Start](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/quick-start) | [quick_start/01_first_frame.py](quick_start/01_first_frame.py) | Network | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/00_receive_image_data.py](camera/00_receive_image_data.py) | Network | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/00_receive_image_data_usb.py](camera/00_receive_image_data_usb.py) | USB | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/01_preview.py](camera/01_preview.py) | Network | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/01_preview_usb.py](camera/01_preview_usb.py) | USB | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/04_jpeg_bytes.py](camera/04_jpeg_bytes.py) | Network | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/02_rgb_arrays.py](camera/02_rgb_arrays.py) | Network | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/02_rgb_arrays_usb.py](camera/02_rgb_arrays_usb.py) | USB | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/03_save_image.py](camera/03_save_image.py) | Network | script |
| [Camera Streaming](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/camera-data-receiving-examples) | [camera/03_save_image_usb.py](camera/03_save_image_usb.py) | USB | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/01_continuous.py](ar/01_continuous.py) | Network | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/01_continuous_usb.py](ar/01_continuous_usb.py) | USB | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/03_display_images.py](ar/03_display_images.py) | Network | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/03_display_images_usb.py](ar/03_display_images_usb.py) | USB | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/04_image_arrays.py](ar/04_image_arrays.py) | Network | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/04_image_arrays_usb.py](ar/04_image_arrays_usb.py) | USB | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/05_pose_matrices.py](ar/05_pose_matrices.py) | Network | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/05_pose_matrices_usb.py](ar/05_pose_matrices_usb.py) | USB | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/10_selected_fields.py](ar/10_selected_fields.py) | Network | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/10_selected_fields_usb.py](ar/10_selected_fields_usb.py) | USB | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/09_intrinsics.py](ar/09_intrinsics.py) | Network | script |
| [AR Data](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/ar-data-receiving-examples) | [ar/09_intrinsics_usb.py](ar/09_intrinsics_usb.py) | USB | script |
| [iPhone IMU](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/imu-data-receiving-examples) | [imu/01_all_sensors.py](imu/01_all_sensors.py) | Network | script |
| [iPhone IMU](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/imu-data-receiving-examples) | [imu/01_all_sensors_usb.py](imu/01_all_sensors_usb.py) | USB | script |
| [iPhone IMU](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/imu-data-receiving-examples) | [imu/02_quick_start.py](imu/02_quick_start.py) | Network | script |
| [iPhone IMU](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/imu-data-receiving-examples) | [imu/02_quick_start_usb.py](imu/02_quick_start_usb.py) | USB | script |
| [Joystick](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/joystick-receiving-example) | [joystick/03_named_controls.py](joystick/03_named_controls.py) | Network | script |
| [Joystick](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/joystick-receiving-example) | [joystick/03_named_controls_usb.py](joystick/03_named_controls_usb.py) | USB | script |
| [Joystick](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/joystick-receiving-example) | [joystick/02_full_controller.py](joystick/02_full_controller.py) | Network | script |
| [Joystick](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/joystick-receiving-example) | [joystick/02_full_controller_usb.py](joystick/02_full_controller_usb.py) | USB | script |
| [Joystick](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/joystick-receiving-example) | [joystick/01_sticks_and_buttons.py](joystick/01_sticks_and_buttons.py) | Network | script |
| [Joystick](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/joystick-receiving-example) | [joystick/01_sticks_and_buttons_usb.py](joystick/01_sticks_and_buttons_usb.py) | USB | script |
| [AirPods Motion](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/airpods-and-gripper) | [airpods/01_rotation.py](airpods/01_rotation.py) | Network | script |
| [AirPods Motion](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/airpods-and-gripper) | [airpods/01_rotation_usb.py](airpods/01_rotation_usb.py) | USB | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/01_all_joints.py](body/01_all_joints.py) | Network | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/01_all_joints_usb.py](body/01_all_joints_usb.py) | USB | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/02_named_joints.py](body/02_named_joints.py) | Network | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/02_named_joints_usb.py](body/02_named_joints_usb.py) | USB | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/03_coordinate_spaces.py](body/03_coordinate_spaces.py) | Network | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/03_coordinate_spaces_usb.py](body/03_coordinate_spaces_usb.py) | USB | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/05_person_id.py](body/05_person_id.py) | Network | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/05_person_id_usb.py](body/05_person_id_usb.py) | USB | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/06_image_landmarks.py](body/06_image_landmarks.py) | Network | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/06_image_landmarks_usb.py](body/06_image_landmarks_usb.py) | USB | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/04_optional_skeleton.py](body/04_optional_skeleton.py) | Network | script |
| [3D Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/body-tracking) | [body/04_optional_skeleton_usb.py](body/04_optional_skeleton_usb.py) | USB | script |
| [2D Upper-Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/upper-body-tracking) | [upper_body/01_relative_joints.py](upper_body/01_relative_joints.py) | Network | script |
| [2D Upper-Body Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/upper-body-tracking) | [upper_body/01_relative_joints_usb.py](upper_body/01_relative_joints_usb.py) | USB | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/01_both_hands.py](hand/01_both_hands.py) | Network | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/01_both_hands_usb.py](hand/01_both_hands_usb.py) | USB | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/02_named_joints_and_pixels.py](hand/02_named_joints_and_pixels.py) | Network | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/02_named_joints_and_pixels_usb.py](hand/02_named_joints_and_pixels_usb.py) | USB | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/04_joint_arrays.py](hand/04_joint_arrays.py) | Network | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/04_joint_arrays_usb.py](hand/04_joint_arrays_usb.py) | USB | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/03_optional_skeleton.py](hand/03_optional_skeleton.py) | Network | script |
| [Hand Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/hand-tracking) | [hand/03_optional_skeleton_usb.py](hand/03_optional_skeleton_usb.py) | USB | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/01_face.py](face/01_face.py) | Network | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/01_face_usb.py](face/01_face_usb.py) | USB | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/02_blendshapes.py](face/02_blendshapes.py) | Network | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/02_blendshapes_usb.py](face/02_blendshapes_usb.py) | USB | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/08_regions_and_box.py](face/08_regions_and_box.py) | Network | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/08_regions_and_box_usb.py](face/08_regions_and_box_usb.py) | USB | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/03_metric_mesh.py](face/03_metric_mesh.py) | Network | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/03_metric_mesh_usb.py](face/03_metric_mesh_usb.py) | USB | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/07_field_types.py](face/07_field_types.py) | Network | script |
| [Face Tracking](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/face-and-hand-tracking) | [face/07_field_types_usb.py](face/07_field_types_usb.py) | USB | script |

## Device checks

The installed diagnostic command checks all supported typed streams, including USB Watch relay and both grippers. It prompts for each app feature and saves a JSON report. Skip channels without the required hardware.

```bash
asmagic-test --all --transport usb --plot --images --report reports/usb.json
asmagic-test --list --transport usb
```

Watch relay requires Watch → iPhone HTTP on port 18002, then iPhone → computer USB. The legacy combined face/hand decoder is available in the SDK; current apps send face and hands independently.

SDK regression tests live in `tests/`; they use synthetic inputs and local transports. They do not establish physical USB behavior or tracking accuracy.

## Keep the code identical

GitBook is the authority for these examples. After changing chapter code, import it and run the drift check:

```bash
python tools/sync_documentation_examples.py --gitbook ../gitbook
python tools/sync_documentation_examples.py --check --gitbook ../gitbook
```

The catalog records the chapter, Python block number, transport and SHA-256 of each file. Add or remove mappings deliberately when chapter blocks change. Do not create independent example implementations.
