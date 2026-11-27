from pathlib import Path
from asmagic import CameraDataSubscriber

with CameraDataSubscriber("192.168.1.100") as camera:
    frame = camera.receive()
    if frame.rgb_codec_name != "jpeg":
        raise ValueError("Select JPEG in Send settings → Encoding.")
    Path("frame.jpg").write_bytes(frame.color_bytes)
