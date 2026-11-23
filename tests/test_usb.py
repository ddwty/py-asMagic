"""Real loopback usbmux protocol tests; no claim of physical USB validation."""
import contextlib
import json
import queue
import socket
import socketserver
import struct
import threading
import time

import pytest
import asmagic
from asmagic.proto import imu_msg_pb2
from asmagic.usb import (_encode, _exact, _extract, _mux, usb_devices,
                         USBConnection, USBPacket, MUX_HEADER)
import plistlib


@pytest.fixture
def mux(monkeypatch):
    received = queue.Queue()
    received.stream_payloads = {"iphone.stream.8002": imu_msg_pb2.Imu(timestamp=33).SerializeToString()}
    stop = threading.Event()

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            sock = self.request
            try:
                size, _, _, _ = MUX_HEADER.unpack(_exact(sock, 16))
                message = plistlib.loads(_exact(sock, size - 16))
                if message["MessageType"] == "ListDevices":
                    result = {"DeviceList": [
                        {"DeviceID": 1, "Properties": {"SerialNumber": "test-usb", "ConnectionType": "USB"}},
                        {"DeviceID": 2, "Properties": {"SerialNumber": "test-wifi", "ConnectionType": "Network"}},
                    ]}
                else:
                    result = {"MessageType": "Result", "Number": 0}
                raw = plistlib.dumps(result)
                sock.sendall(MUX_HEADER.pack(len(raw) + 16, 1, 8, 1) + raw)
                if message["MessageType"] == "ListDevices":
                    return
                if message.get("PortNumber") == socket.htons(62078):
                    values = dict(DeviceName="Test iPhone", DeviceClass="iPhone", ProductType="iPhone18,1")
                    while not stop.is_set():
                        size, = struct.unpack("!I", _exact(sock, 4))
                        request = plistlib.loads(_exact(sock, size))
                        raw = plistlib.dumps(dict(Value=values[request["Key"]]))
                        sock.sendall(struct.pack("!I", len(raw)) + raw)
                    return
                sock.sendall(_encode(dict(kind="hello", role="phone", protocol="asmagic-usb-v1")))
                sock.settimeout(.05)
                buffer = bytearray()
                while not stop.is_set():
                    for topic, payload in list(received.stream_payloads.items()):
                        sock.sendall(_encode(dict(kind="data", topic=topic, content_type="application/octet-stream"), payload))
                    try:
                        chunk = sock.recv(65536)
                        if not chunk:
                            break
                        buffer.extend(chunk)
                        for packet in _extract(buffer):
                            received.put(packet)
                            if packet.header["kind"] == "request":
                                sock.sendall(_encode(dict(kind="response", reply_to=packet.header["id"], ok=True), b'{"name":"Test iPhone"}'))
                            elif packet.header["kind"] == "ping":
                                sock.sendall(_encode(dict(kind="pong")))
                            elif packet.header["kind"] == "catalog":
                                for channel in packet.header["channels"]:
                                    if channel.get("mode") == "command":
                                        sock.sendall(_encode(dict(kind="request", topic=channel["topic"], id="host-command"), b'{"value":7}'))
                    except socket.timeout:
                        pass
            except (OSError, ConnectionError):
                pass

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = True

    server = Server(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = "tcp://127.0.0.1:{}".format(server.server_address[1])
    monkeypatch.setenv("ASMagic_USBMUX_ADDRESS", address)
    yield address, received
    stop.set()
    server.shutdown()
    server.server_close()
    thread.join()


def wait_connected(link):
    deadline = time.monotonic() + 3
    while not link.is_connected and time.monotonic() < deadline:
        time.sleep(.01)
    assert link.is_connected, link.last_error


def test_devices_exclude_wifi_and_work_over_tcp_daemon(mux):
    assert usb_devices(details=False) == [{"id": 1, "udid": "test-usb"}]
    assert usb_devices() == [dict(id=1, udid="test-usb", host="usb:test-usb", name="Test iPhone",
                                  device_type="iPhone", product_type="iPhone18,1")]


def test_auto_usb_rejects_multiple_apple_devices_instead_of_picking_first(mux, monkeypatch):
    monkeypatch.setattr("asmagic.usb.usb_devices", lambda *args, **kwargs:
                        [dict(id=1, udid="phone-1"), dict(id=2, udid="phone-2")])
    with USBConnection() as link:
        with pytest.raises(TimeoutError, match="Several Apple USB devices.*phone-1, phone-2"):
            link.wait_connected(timeout=.1)
        assert not link.is_connected


def test_auto_usb_keeps_device_identity_after_disconnect(mux, monkeypatch):
    with USBConnection() as link:
        link.wait_connected(timeout=3)
        assert link.device_udid == "test-usb"
        monkeypatch.setattr("asmagic.usb.usb_devices", lambda *args, **kwargs:
                            [dict(id=2, udid="different-phone")])
        link._socket.shutdown(socket.SHUT_RDWR)
        deadline = time.monotonic() + 2
        while link.is_connected and time.monotonic() < deadline:
            time.sleep(.01)
        with pytest.raises(TimeoutError):
            link.wait_connected(timeout=1.2)
        assert link.device_udid == "test-usb"


def test_typed_imu_uses_usb_without_ip_and_preserves_decoding(mux):
    with asmagic.subscribe("imu", transport="usb", udid="test-usb") as receiver:
        frame = receiver.receive(timeout=3000)
        assert frame is not None and frame.timestamp == 33
        assert receiver.address == "usb://test-usb/8002"
        assert receiver.has_received_data


def test_explicit_subscriber_usb_alias_is_backwards_compatible(mux):
    with asmagic.IMUDataSubscriber("usb") as receiver:
        assert receiver.receive(timeout=3000).timestamp == 33


def test_usb_wait_connected_returns_only_after_phone_hello(mux):
    with USBConnection("test-usb") as link:
        assert link.wait_connected(timeout=3) is link
        assert link.request("phone.status") == {"name": "Test iPhone"}
    with pytest.raises(ConnectionError, match="closed"):
        link.wait_connected()


def test_usb_wait_connected_times_out_with_recovery_hint(mux):
    with USBConnection("not-attached") as link:
        with pytest.raises(TimeoutError):
            link.wait_connected(timeout=.05)
        with pytest.raises(ValueError):
            link.wait_connected(timeout=float("nan"))


def test_bidirectional_raw_data_publish_and_acknowledgement(mux):
    _, received = mux
    with USBConnection("test-usb") as link:
        wait_connected(link)
        link.publish("pi.test.force", {"force": [1, 2, 3]}, name="Force")
        assert link.request("phone.status") == {"name": "Test iPhone"}
        packet = link.receive(timeout=2)
        assert isinstance(packet, USBPacket)
        assert packet.topic == "iphone.stream.8002"
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            packet = received.get(timeout=2)
            if packet.header["kind"] == "data":
                assert json.loads(packet.payload) == {"force": [1, 2, 3]}
                break
        else:
            pytest.fail("No host-to-phone data")


def test_disconnected_command_is_not_queued(mux):
    with USBConnection("not-attached") as link:
        with pytest.raises(ConnectionError, match="not queued"):
            link.request("phone.status")


def test_typed_receiver_waits_for_late_usb_attachment_instead_of_failing(mux):
    with asmagic.subscribe("imu", transport="usb", udid="not-attached") as receiver:
        assert receiver.receive(timeout=100) is None
        assert receiver.is_connected  # subscription open, not proof of delivery


def test_host_command_handler_and_response(mux):
    _, received = mux
    calls = []
    with USBConnection("test-usb") as link:
        wait_connected(link)
        def handle(value):
            calls.append(value)
            return {"returned": value["value"]}
        link.register_command("pi.test.echo", handle, name="Echo")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            packet = received.get(timeout=2)
            if packet.header["kind"] == "response":
                assert packet.header["ok"]
                assert json.loads(packet.payload) == {"returned": 7}
                break
        else:
            pytest.fail("No command response")
        assert calls == [{"value": 7}]


@pytest.mark.parametrize("udid", [None, "broker-phone"])
def test_local_broker_sharing_does_not_claim_usb_before_phone_hello(monkeypatch, udid):
    import os
    import tempfile
    if os.name == "nt":
        pytest.skip("Local Pi broker is a Unix-socket feature")
    release_phone = threading.Event()
    with tempfile.TemporaryDirectory(prefix="usb-bus-", dir="/tmp") as directory:
        path = directory + "/bus"
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(path)
        listener.listen(1)
        def server():
            conn, _ = listener.accept()
            with conn:
                conn.sendall(_encode(dict(kind="hello", role="bridge", protocol="asmagic-usb-v1")))
                conn.sendall(_encode(dict(kind="catalog", channels=[], usb_connected=False, device_udid="broker-phone")))
                release_phone.wait(2)
                conn.sendall(_encode(dict(kind="catalog", channels=[], usb_connected=True, device_udid="broker-phone")))
                while conn.recv(65536):
                    pass
        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        monkeypatch.setenv("ASMagic_USB_BRIDGE_SOCKET", path)
        with USBConnection(udid) as link:
            time.sleep(.1)
            assert not link.is_connected
            release_phone.set()
            wait_connected(link)
            assert link._local_bridge
        listener.close()
        thread.join(2)


def test_explicit_udid_bypasses_broker_for_a_different_phone(mux, monkeypatch, tmp_path):
    import os
    if os.name == "nt":
        pytest.skip("Pi broker uses Unix sockets")
    # Keep the Unix socket path within macOS's length limit.
    import tempfile
    with tempfile.TemporaryDirectory(dir="/tmp") as directory:
        path = directory + "/bus"
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(path)
        listener.listen(1)
        def serve():
            conn, _ = listener.accept()
            with conn:
                conn.sendall(_encode(dict(kind="hello", role="bridge", protocol="asmagic-usb-v1")))
                conn.sendall(_encode(dict(kind="catalog", channels=[], usb_connected=True, device_udid="other-phone")))
                with contextlib.suppress(OSError):
                    while conn.recv(65536):
                        pass
        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        monkeypatch.setenv("ASMagic_USB_BRIDGE_SOCKET", path)
        with USBConnection("test-usb") as link:
            link.wait_connected(timeout=3)
            assert not link._local_bridge
            assert link.device_udid == "test-usb"
            assert link.request("phone.status") == {"name": "Test iPhone"}
        listener.close()
        thread.join(2)


def test_oversize_is_rejected_before_allocating_payload():
    from asmagic.usb import FRAME_HEADER, MAX_PAYLOAD
    with pytest.raises(ValueError):
        _extract(bytearray(FRAME_HEADER.pack(2, MAX_PAYLOAD + 1)))


def test_fragmented_binary_payload_is_not_corrupted():
    raw = _encode(dict(kind="data", topic="pi.image"), bytes(range(256)))
    buffer = bytearray()
    result = []
    for offset in range(0, len(raw), 3):
        buffer.extend(raw[offset:offset + 3])
        result.extend(_extract(buffer))
    assert len(result) == 1 and result[0].payload == bytes(range(256))


def test_factory_rejects_invalid_route():
    with pytest.raises(ValueError, match="transport"):
        asmagic.subscribe("imu", transport="serial")
