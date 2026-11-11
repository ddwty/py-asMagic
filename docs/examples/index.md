# Runnable documentation examples

Each documentation example has its own independent `.py` file in `examples/documentation/`.
The Python code blocks on these pages are copied verbatim from those files. They import the installed SDK
directly, without `_common.py`, CLI arguments, a test runner or fixtures.
Basic loops use `receive()`, which waits for a valid frame. Use `receive(timeout=...)` for timeouts.

## Install the local SDK

From the project directory containing `pyproject.toml`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows, activate with `.venv\Scripts\activate`. Python 3.8+ is supported.
The default installation includes Matplotlib for skeleton plots and PyAV for HEVC images, along with every other runtime dependency.
Users do not need to choose extras. Displaying a skeleton remains an API choice, off by default.
These examples target SDK 1.0.2 or newer. Install it with `python -m pip install --upgrade "asmagic>=1.0.2"`.

## Run each example yourself

1. Open the feature being tested in the App and start its data output.
2. For ZeroMQ examples, replace `IPHONE_IP = "192.168.1.100"` with the iPhone address on the same LAN.
3. For Watch, start the Python receiver and set the Watch destination to this computer's LAN IP and listening port.
4. Run the corresponding file from the project directory; Ctrl-C stops receiving.

```bash
python examples/documentation/ar/01_continuous.py
python examples/documentation/body/04_optional_skeleton.py
python examples/documentation/hand/03_optional_skeleton.py
```

Camera features can need separate sessions; test one feature at a time. These scripts never mark a real App
test as passed. Check the printed values and compare plots with your actual actions.

## Choose whether to display a skeleton

Body, upper-body, hand and face/hand pages include a complete optional plotting example.
Set `SHOW_SKELETON = True` to display the figure or `False` to receive only.
The standard examples receive with receive(); no window is created when SHOW_SKELETON=False.
Use `PLOT_OPTIONS` to set labels, drawing frequency and stale-data timeout;
3D body plots support body or world coordinates. Plots run on the main thread.
`CameraFrame.color_bytes` returns encoded JPEG/HEVC data. Use `data.show_image()` to display an upright camera image.

## Pages and files

| Documentation page | Files | Examples |
|---|---|---:|
| [Camera Streaming Examples](camera.md) | [camera/](../../examples/documentation/camera/) | 4 |
| [AR Data Receiving Examples](ar.md) | [ar/](../../examples/documentation/ar/) | 10 |
| [IMU Data Receiving Examples](imu.md) | [imu/](../../examples/documentation/imu/) | 2 |
| [Joystick Receiving Examples](joystick.md) | [joystick/](../../examples/documentation/joystick/) | 3 |
| [AirPods Receiving Examples](airpods.md) | [airpods/](../../examples/documentation/airpods/) | 1 |
| [Body Tracking Receiving Examples](body.md) | [body/](../../examples/documentation/body/) | 6 |
| [Upper Body Receiving Examples](upper_body.md) | [upper_body/](../../examples/documentation/upper_body/) | 2 |
| [Hand Tracking Receiving Examples](hand.md) | [hand/](../../examples/documentation/hand/) | 4 |
| [Face Data Receiving Examples](face.md) | [face/](../../examples/documentation/face/) | 7 |
| [Gripper Receiving Examples](claw.md) | [claw/](../../examples/documentation/claw/) | 2 |
| [Watch IMU Receiving Examples](watch.md) | [watch/](../../examples/documentation/watch/) | 4 |
| [Common Receiving API Examples](common.md) | [common/](../../examples/documentation/common/) | 7 |
| [Skeleton Plotting API Examples](plotting.md) | [plotting/](../../examples/documentation/plotting/) | 4 |
| [Legacy Receiving Examples](legacy.md) | [legacy/](../../examples/documentation/legacy/) | 2 |

See [Data Format and API](api-reference.md) for method signatures, return values, units and missing-data behavior.
The [joint catalog](joint-catalog.md) lists the available body/hand joints, Python paths and array rows.
Legacy pages are compatibility examples for old publishers with known ports, not current App features.

## Keep documentation and executable code identical

The source of each Python block is its standalone file; its title and notes are in
`examples/documentation/catalog.json`. After editing a file or note:

```bash
python tools/sync_documentation_examples.py
python tools/sync_documentation_examples.py --check
```

The first command updates Markdown pages. The second verifies that synchronized code and tables match their
source files. All inputs and generated pages are contained in this repository.
The separate `examples/test_app_streams.py` guided diagnostic tool remains available; it is not required for these examples.
