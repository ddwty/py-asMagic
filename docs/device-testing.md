# Test app streams

Use the [chapter examples](../examples/documentation/README.md) to run the exact code shown in GitBook, including separate USB files. Use `asmagic-test` for guided checks and JSON reports.

## USB device checks

Install this checkout from the directory containing `pyproject.toml`:

```bash
python -m pip install -e .
asmagic usb list
asmagic-test --list --transport usb
asmagic-test --all --transport usb --plot --images --report reports/usb.json
```

Connect a USB data cable, unlock and trust the computer, and keep asMagic in the foreground. Start the matching app output for each step. With multiple Apple devices attached, add `--udid DEVICE_UDID` using the identifier from `asmagic usb list`. System setup and troubleshooting are in [USB support](USB.md).

The sequence includes camera, AR images/depth/pose, AirPods, iPhone IMU, upper body, joystick, native AR body, unified ARKit and MediaPipe body, hands, face, both grippers and Watch relay. Skip channels without the required hardware. Current apps send face and hands independently; `face_hand` is an optional single-stream check for legacy combined publishers and is excluded from `--all`.

Watch relay uses **Watch → iPhone HTTP on port 18002 → computer USB**. Set the Watch destination to the iPhone's LAN IP, keep the iPhone app open, and start the Watch check before sending. The Watch-to-iPhone hop still requires network connectivity.

```bash
asmagic-test imu --transport usb --count 100
asmagic-test camera --transport usb --images
asmagic-test body_mediapipe --transport usb --plot
asmagic-test watch --transport usb
asmagic-test face_hand --transport usb
```

## Network device checks

```bash
asmagic-test --all --ip 192.168.1.100 --plot --images --report reports/network.json
asmagic-test hand --ip 192.168.1.100 --plot
asmagic-test watch --bind 0.0.0.0 --port 8002
```

For network Watch reception, set the Watch destination to the **computer's LAN IP**, not the iPhone or `0.0.0.0`. `--watch-port` changes its listening port in a guided sequence; `--port` overrides a single check's port.

## Read the results

Guided mode requires an interactive terminal. Enter starts a check, `s` skips it, and `q` ends the sequence. Each check defaults to 15 seconds; `--duration 30` changes the limit and `--count 100` ends after 100 frames. The tool saves the report after each step. Ctrl-C closes the receiver and saves the current results.

`--plot` displays tracking skeletons; `--images` displays camera images. `--space world` selects world coordinates for body plots. Missing world transforms stay unavailable. GUI windows need a desktop environment and run on the main thread on macOS.

| Status | Meaning |
|---|---|
| `received` | Valid fields received without detected errors |
| `received_with_errors` | Valid data and one or more receive/decode/field errors |
| `empty_data` | Frames arrived without usable sensor or tracking results |
| `no_data` | No frames arrived within the time limit |
| `errors` | Receive, decode or field checks failed |
| `skipped` / `not_run` | Manually skipped / not executed |

The report records frame counts, sample counts, receive rate, field presence, errors and last values. Watch counts batches and samples separately. Guided mode also records whether your movements matched the displayed values. Receiving bytes does not establish tracking accuracy; compare values and plots with actual movements.

## SDK regression checks

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python tools/sync_documentation_examples.py --check --gitbook ../gitbook
```

`tests/` contains SDK regression checks using synthetic inputs and local TCP/HTTP/usbmux services. They do not require a connected phone and do not validate physical USB behavior. The synchronization check compares every mapped GitBook Python block with its local file, hash and generated reference. It rejects missing chapters, missing blocks and divergent code.

To export synthetic skeleton previews without a device, run `python tools/preview_tracking_plots.py`. The images are explicitly labeled as fixtures.
