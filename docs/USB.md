# USB reception and duplex data

Requires SDK 1.1.0+ and an asMagic iPhone build that includes **USB devices**.

## Change the IP to "usb"

Existing classes, `receive()`, iteration and frame fields keep the same API:

```python
import asmagic

# Network: asmagic.IMUDataSubscriber("192.168.1.100")
with asmagic.IMUDataSubscriber("usb") as sub:
    for frame in sub:
        print(frame.timestamp, frame.accelerometer, frame.gyroscope)
```

The same replacement works with `CameraDataSubscriber`, `ARDataSubscriber`,
hand, face, body, joystick, AirPods and gripper stream subscribers. Start the
corresponding Stream in the iPhone app to send its data.

The stream factory also supports either form:

```python
sub = asmagic.subscribe("imu", "usb")
sub.close()
sub = asmagic.subscribe("imu", transport="usb")
sub.close()
```

Phone USB-C → computer USB host port is the physical connection. Use a data
cable, unlock iPhone, accept the first-use trust prompt and keep asMagic in
the foreground. A Pi 5 uses its USB-A port or a host hub; its USB-C supply
input is for power.

## Install on a new computer

Install the SDK:

```bash
python -m pip install --upgrade "asmagic>=1.1.0"
asmagic usb list
```

All USB Python code and the discovery/setup commands ship in this package.

| Host | System USB support | First-use setup |
| --- | --- | --- |
| macOS | Apple's built-in USB service | Connect, unlock and trust the Mac |
| Windows | Apple Devices and Apple Mobile Device Service | `asmagic usb setup` invokes the Microsoft Store installer through winget |
| Linux / Raspberry Pi OS | usbmuxd and libimobiledevice pairing tools | `asmagic usb setup` installs system packages and starts usbmuxd on systemd hosts |

Python package installation handles Python dependencies. System services and
Windows device drivers require the OS installer and its administrator prompts.
`asmagic usb setup --print-only` shows the commands before executing them.
Linux automated setup supports apt, dnf and pacman; other distributions use
their package manager to install usbmuxd and libimobiledevice.

When one phone is attached and `idevicepair` is available, setup also attempts
pairing. Accept the trust prompt and repeat setup if pairing is still pending.
For a host with several phones, pair a selected phone using
`idevicepair -u DEVICE_UDID pair`.

```bash
asmagic usb doctor
asmagic usb list --json
asmagic-test imu --transport usb --count 100
asmagic-test camera --transport usb --images
```

Discovery lists physical USB devices; application readiness is established
when the app handshake completes and a Stream supplies data.

## Discover and select a phone

General USB peripherals such as cameras, keyboards and disks are outside
Apple's usbmux device list. Discovery returns USB-connected Apple devices,
including iPhone and iPad; `device_type` identifies the device class.

With one Apple USB device attached, `"usb"` selects it automatically. If several
are attached at the first selection, reception waits with an explicit selection
error. It never chooses the first row. Once selected, an automatic session
keeps that UDID through reconnects until the session is closed.

Read display names and stable identifiers from Python:

```python
import asmagic

for device in asmagic.usb_devices():
    print(device["name"], device["device_type"], device["udid"], device["host"])
# Example: iPhone 17 Pro 1, iPhone, DEVICE_UDID, usb:DEVICE_UDID
print(asmagic.usb_status())   # service_available, devices, error, next_action
```

`usb_devices()` raises a connection error with setup instructions if the system
USB service is unavailable. `usb_status()` returns that diagnosis as a dictionary.

Device names are display labels and can be changed or duplicated. Persist
the **UDID** for a known phone. The numeric `id` belongs to the current USB
attachment and can change after reconnecting. `host` is the ready-to-use
`"usb:DEVICE_UDID"` connection string.

Identity lookup uses Apple's device service; if it is unavailable, discovery
keeps the UDID and reports `identity_error` with nullable name/model fields.
`usb_devices(details=False)` returns only numeric IDs and UDIDs for fast polling.

With several phones or a phone plus iPad, pass `"usb:DEVICE_UDID"` in place of the IP:

```python
with asmagic.IMUDataSubscriber("usb:DEVICE_UDID") as sub:
    frame = sub.receive()
    print(frame.accelerometer)
```

The factory equivalent is
`asmagic.subscribe("imu", transport="usb", udid="DEVICE_UDID")`.

## Send data and receive acknowledged commands

```python
import asmagic

with asmagic.USBConnection() as phone:
    phone.wait_connected(timeout=10)  # seconds; raises with connection guidance
    print(phone.request("phone.status"))
    phone.publish("pi.force", {"value": 2.4, "unit": "N"}, name="Force")
    while True:
        packet = phone.receive(timeout=1)
        if packet is not None:
            print(packet.topic, len(packet.payload))
```

The `pi.` topic prefix names host data on every supported computer. Publish
JPEG bytes with `content_type="image/jpeg"` for image preview. The app's
**USB devices** page displays incoming JPEG/JSON channels; arbitrary binary
payloads keep their original bytes. Rich views for additional semantic
formats use adapters/renderers.

Register an explicit host command with
`phone.register_command(topic, handler)`. The app lists it under Device
commands; handlers own hardware stop/cleanup behavior.

## Shared sessions and recovery

Typed readers in one Python process share a physical USB session per UDID.
On a Pi with `/run/asmagic-usb/bus.sock`, `"usb"` shares its optional existing
broker. An explicit `"usb:UDID"` also shares that broker when its selected UDID
matches. A different explicit UDID connects to that phone directly. The separate `asmagic-usb-link` service supplies boot startup, camera
hotplug and adapters for local sensors. Basic iPhone Stream reception uses
the SDK directly on a host with system USB support.

For a broker with several Apple devices, set `device_udid` in its configuration
to choose the phone used by the bridge's sensors and controls. An unconfigured broker waits when the initial
choice is ambiguous. Its automatic selection keeps the first unique UDID for
the service lifetime; configure a UDID to preserve the choice across restarts.
`ASMagic_USB_BRIDGE_SOCKET` overrides the local bus path.
`ASMagic_USBMUX_ADDRESS` overrides the system USB service endpoint with a
Unix socket path or `tcp://127.0.0.1:27015`.

Subscribers may start before attachment and wait for the phone. USB disconnect
clears stale data and retries the link. Pending commands fail on disconnect;
a new intentional request is required after recovery. AR/camera packets stay
ordered before decoding; bounded queue overflow resets the link and reports
an error. Starting a Stream and saving recordings remain explicit app actions.
Watch also accepts `WatchIMUReceiver("usb")` or `"usb:DEVICE_UDID"`. Set the
Watch HTTP sender to the iPhone's LAN IP and port **18002**; the USB-enabled
foreground app forwards the original batches as `iphone.watch.8002`. The
receiver's logical port stays 8002. Direct Watch HTTP to a computer remains
available through `WatchIMUReceiver("0.0.0.0", port=8002)`.

Raw audio and additional binary channels are available through
`USBConnection.receive()`, including `iphone.websocket.8081`. Typed extra
protobuf ports use `ProtobufSubscriber("usb", port, message_type)`.

## Hardware verification

On 2026-11-23, iPhone 17 Pro 1 → Raspberry Pi USB request/reply succeeded;
IMU reception measured 601 packets in 10 seconds (about 60 Hz). The SDK also
decoded 60 actual IMU frames through the Pi broker. Windows and direct Mac
iPhone USB data, Watch hardware, camera throughput and unplug/replug recovery
await validation. The local Watch relay smoke check covers fragmented/bounded
HTTP requests and unchanged USB payloads.

See the [GitBook command reference](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/command-line) for every CLI action and option.
