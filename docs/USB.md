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

[Complete command reference](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/command-line)
