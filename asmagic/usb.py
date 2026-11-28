"""Duplex USB transport through the host's Apple/usbmuxd service (stdlib only).

macOS/Linux use a Unix socket; Windows uses Apple Mobile Device Service's
loopback TCP endpoint. Pair/trust the iPhone once and keep asMagic foregrounded.
"""
from dataclasses import dataclass
import contextlib
import json
import math
import os
import plistlib
import queue
import select
import socket
import struct
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

MAX_HEADER = 65536
MAX_PAYLOAD = 32 * 1024 * 1024
MUX_HEADER = struct.Struct("<IIII")
FRAME_HEADER = struct.Struct("!II")


@dataclass
class USBPacket:
    header: dict
    payload: bytes

    @property
    def topic(self):
        return self.header.get("topic", "")


def _exact(sock, size):
    result = bytearray()
    while len(result) < size:
        chunk = sock.recv(size - len(result))
        if not chunk:
            raise ConnectionError("USB connection closed")
        result.extend(chunk)
    return bytes(result)


def _daemon(address=None):
    address = address or os.environ.get("ASMagic_USBMUX_ADDRESS")
    if address is None:
        address = ("127.0.0.1", 27015) if sys.platform == "win32" else "/var/run/usbmuxd"
    if isinstance(address, str) and address.startswith("tcp://"):
        host, port = address[6:].rsplit(":", 1)
        address = (host, int(port))
    result = None
    try:
        if isinstance(address, tuple):
            return socket.create_connection(address, 3)
        result = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        result.settimeout(3)
        result.connect(address)
        return result
    except BaseException as error:
        if result is not None:
            result.close()
        if isinstance(error, OSError):
            from .usb_host import setup_hint
            raise ConnectionError("Cannot reach USB service at {}: {}. {}".format(
                address, error, setup_hint())) from error
        raise


def _mux(message, address=None):
    sock = _daemon(address)
    try:
        raw = plistlib.dumps(dict(message, ClientVersionString="asmagic/usb-v1", ProgName="asmagic", kLibUSBMuxVersion=3))
        sock.sendall(MUX_HEADER.pack(len(raw) + 16, 1, 8, 1) + raw)
        size, version, kind, tag = MUX_HEADER.unpack(_exact(sock, 16))
        if not 16 < size <= 1024 * 1024 or (version, kind, tag) != (1, 8, 1):
            raise ValueError("Invalid usbmuxd response")
        response = plistlib.loads(_exact(sock, size - 16))
        return response, sock
    except BaseException:
        sock.close()
        raise


def _device_info(device_id, address=None):
    """Read display identity from Apple's lockdown service, independently of the app."""
    info = dict(name=None, device_type=None, product_type=None)
    sock = None
    try:
        response, sock = _mux(dict(MessageType="Connect", DeviceID=device_id,
                                   PortNumber=socket.htons(62078)), address)
        if response.get("Number") != 0:
            raise ConnectionError("Device identity service unavailable; unlock and trust this computer")
        for key, field in (("DeviceName", "name"), ("DeviceClass", "device_type"), ("ProductType", "product_type")):
            raw = plistlib.dumps(dict(Label="asmagic", Request="GetValue", Key=key))
            sock.sendall(struct.pack("!I", len(raw)) + raw)
            size, = struct.unpack("!I", _exact(sock, 4))
            if not 0 < size <= 1024 * 1024:
                raise ValueError("Invalid USB device identity response")
            value = plistlib.loads(_exact(sock, size))
            if isinstance(value.get("Value"), str):
                info[field] = value["Value"]
            elif value.get("Error"):
                info["identity_error"] = str(value["Error"])
    except (OSError, ValueError) as error:
        info["identity_error"] = str(error)
    finally:
        if sock:
            sock.close()
    return info


def usb_devices(address=None, *, details=True):
    """List physical Apple USB devices (iPhone/iPad), with stable UDID and name.

    details=False skips optional identity queries. Discovery excludes network
    peers and general USB peripherals. Names are display labels; use the host
    string or UDID to select a specific device.
    """
    response, sock = _mux({"MessageType": "ListDevices"}, address)
    sock.close()
    devices = [dict(id=item["DeviceID"], udid=item["Properties"].get("SerialNumber", ""))
               for item in response.get("DeviceList", []) if item.get("Properties", {}).get("ConnectionType") == "USB"]
    if details:
        for device in devices:
            device.update(_device_info(device["id"], address))
            device["host"] = "usb:" + device["udid"]
    return devices


def _encode(header, payload=b""):
    raw = json.dumps(dict(header, v=1), separators=(",", ":"), allow_nan=False).encode()
    if not 0 < len(raw) <= MAX_HEADER or len(payload) > MAX_PAYLOAD:
        raise ValueError("USB frame exceeds size limit")
    return FRAME_HEADER.pack(len(raw), len(payload)) + raw + payload


def _extract(buffer):
    packets = []
    while len(buffer) >= 8:
        header_size, payload_size = FRAME_HEADER.unpack_from(buffer)
        if not 0 < header_size <= MAX_HEADER or payload_size > MAX_PAYLOAD:
            raise ValueError("Invalid USB frame size")
        total = 8 + header_size + payload_size
        if len(buffer) < total:
            break
        payload_start = FRAME_HEADER.size + header_size
        header = json.loads(buffer[FRAME_HEADER.size:payload_start])
        if not isinstance(header, dict) or header.get("v") != 1:
            raise ValueError("Unsupported USB protocol version")
        with memoryview(buffer) as view:
            payload = bytes(view[payload_start:total])
        packets.append(USBPacket(header, payload))
        del buffer[:total]
    return packets


class USBConnection:
    """One reconnecting physical link, with extensible publish/subscribe/RPC.

    Reconnection never resends commands. Existing typed receivers share this
    connection per UDID. Generic users should close it or use a with block.
    """

    def __init__(self, udid=None, *, usbmux_address=None, phone_port=49170):
        self.udid, self.usbmux_address, self.phone_port = udid, usbmux_address, phone_port
        self.device_udid = udid
        self.is_connected = False
        self.last_error = None
        self.channels = {}
        self._socket = None
        self._lock = threading.RLock()
        self._send_lock = threading.Lock()
        self._stop = threading.Event()
        self._callbacks = {}
        self._pending = {}
        self._packets = None
        self._handlers = {}
        self._executing = set()
        self._generation = None
        self._local_bridge = False
        self._bypass_broker = False
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="asmagic-usb-command")
        self._thread = threading.Thread(target=self._run, name="asmagic-usb", daemon=True)
        self._thread.start()

    def _send(self, header, payload=b"", sock=None):
        with self._send_lock:
            target = sock or self._socket
            if target is None or (sock is None and not self.is_connected):
                raise ConnectionError("USB is disconnected; command was not queued")
            target.sendall(_encode(header, payload))

    def wait_connected(self, timeout=10):
        """Wait up to timeout seconds for an app handshake; return self or raise."""
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0:
            raise ValueError("timeout must be finite and nonnegative, in seconds")
        deadline = time.monotonic() + timeout
        while not self.is_connected:
            if self._stop.is_set():
                raise ConnectionError("USB connection is closed")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(self.last_error or "Waiting for a USB iPhone; unlock, trust and open asMagic")
            self._stop.wait(min(.05, remaining))
        return self

    def _run(self):
        while not self._stop.is_set():
            sock = None
            had_session = False
            try:
                bridge = os.environ.get("ASMagic_USB_BRIDGE_SOCKET", "/run/asmagic-usb/bus.sock")
                self._local_bridge = not self._bypass_broker and os.name != "nt" and os.path.exists(bridge)
                if self._local_bridge:
                    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    sock.connect(bridge)
                    self._send(dict(kind="hello", role="sensor", name="py-asMagic"), sock=sock)
                    self._send(dict(kind="subscribe", topics=["*"]), sock=sock)
                else:
                    devices = usb_devices(self.usbmux_address, details=False)
                    if self.device_udid:
                        devices = [d for d in devices if d["udid"] == self.device_udid]
                    if not devices:
                        raise ConnectionError("USB iPhone not attached; connect, unlock, trust and open asMagic")
                    if len(devices) > 1:
                        raise ConnectionError("Several Apple USB devices attached; select usb:UDID using asmagic usb list. Candidates: "
                                              + ", ".join(d["udid"] for d in devices))
                    self.device_udid = devices[0]["udid"]
                    response, sock = _mux({"MessageType": "Connect", "DeviceID": devices[0]["id"],
                                           "PortNumber": socket.htons(self.phone_port)}, self.usbmux_address)
                    if response.get("Number") != 0:
                        raise ConnectionError("Open the updated asMagic app on the USB iPhone (usbmux code {})".format(response.get("Number")))
                    self._send(dict(kind="hello", role="bridge", name=socket.gethostname(), protocol="asmagic-usb-v1"), sock=sock)
                buffer = bytearray()
                received = last_ping = time.monotonic()
                self._socket = sock
                generation = self._generation = str(uuid.uuid4())
                while not self._stop.is_set():
                    readable, _, _ = select.select([sock], [], [], 0.2)
                    if readable:
                        chunk = sock.recv(65536)
                        if not chunk:
                            raise ConnectionError("USB phone disconnected")
                        buffer.extend(chunk)
                        for packet in _extract(buffer):
                            received = time.monotonic()
                            if packet.header.get("kind") == "hello":
                                if packet.header.get("role") != ("bridge" if self._local_bridge else "phone") or packet.header.get("protocol") != "asmagic-usb-v1":
                                    raise ValueError("Unexpected USB peer")
                                self.is_connected = not self._local_bridge
                                had_session = self.is_connected
                                self.last_error = None
                                with self._lock:
                                    catalog = list(self.channels.values())
                                if catalog and not self._local_bridge:
                                    self._send(dict(kind="catalog", channels=catalog), sock=sock)
                                elif self._local_bridge:
                                    for descriptor in catalog:
                                        self._send(dict(descriptor, kind="advertise"), sock=sock)
                            elif packet.header.get("kind") == "catalog" and self._local_bridge:
                                connected = bool(packet.header.get("usb_connected"))
                                selected = packet.header.get("device_udid")
                                if self.device_udid and selected != self.device_udid:
                                    # Share a broker only when it owns the requested phone.
                                    # Otherwise connect that UDID directly on the next attempt.
                                    self._bypass_broker = True
                                    raise ConnectionError("USB broker owns another device; connecting selected UDID directly")
                                if connected and selected:
                                    self.device_udid = selected
                                if self.is_connected and not connected:
                                    self._notify_disconnect("USB phone disconnected")
                                self.is_connected = connected
                                had_session = had_session or connected
                            elif packet.header.get("kind") == "ping":
                                self._send(dict(kind="pong"), sock=sock)
                            elif packet.header.get("kind") == "response":
                                with self._lock:
                                    waiter = self._pending.pop(packet.header.get("reply_to"), None)
                                if waiter:
                                    waiter.put_nowait(packet)
                            elif packet.header.get("kind") == "data" and self.is_connected:
                                with self._lock:
                                    callbacks = list(self._callbacks.values())
                                for callback in callbacks:
                                    callback(packet)
                            elif packet.header.get("kind") == "request":
                                with self._lock:
                                    if len(self._executing) >= 32:
                                        raise RuntimeError("Too many pending host commands")
                                    future = self._executor.submit(self._command, packet, generation)
                                    self._executing.add(future)
                                    future.add_done_callback(self._command_done)
                    now = time.monotonic()
                    if now - received > 8:
                        raise TimeoutError("USB peer heartbeat expired")
                    if (self.is_connected or self._local_bridge) and now - last_ping >= 0.5:
                        self._send(dict(kind="ping"), sock=sock)
                        last_ping = now
            except Exception as error:
                self.last_error = str(error)
                if had_session:
                    self._notify_disconnect(str(error))
            finally:
                self.is_connected = False
                self._socket = None
                self._generation = None
                if sock:
                    sock.close()
            self._stop.wait(1)

    def _notify_disconnect(self, message):
        self.last_error = message
        with self._lock:
            callbacks = list(self._callbacks.values())
            pending, self._pending = list(self._pending.values()), {}
        for waiter in pending:
            with contextlib.suppress(queue.Full):
                waiter.put_nowait(ConnectionError("USB disconnected; command was not replayed"))
        for callback in callbacks:
            with contextlib.suppress(Exception):
                callback(ConnectionError(message))

    def publish(self, topic, value, *, name=None, content_type="application/json"):
        """Send a sensor sample to iPhone; JPEG and arbitrary bytes are supported."""
        if not isinstance(topic, str) or not topic.startswith("pi."):
            raise ValueError("Host sensor topics must begin with pi.")
        payload = json.dumps(value, allow_nan=False).encode() if content_type == "application/json" else bytes(value)
        with self._lock:
            descriptor = dict(topic=topic, name=name or topic, content_type=content_type)
            if self.channels.get(topic) != descriptor:
                self.channels[topic] = descriptor
                self._send(dict(descriptor, kind="advertise") if self._local_bridge else dict(kind="catalog", channels=list(self.channels.values())))
        self._send(dict(kind="data", topic=topic, content_type=content_type), payload)

    def register_command(self, topic, handler, name=None):
        """Expose an explicit JSON command; arbitrary shell execution is never provided."""
        with self._lock:
            self._handlers[topic] = handler
            self.channels[topic] = dict(topic=topic, name=name or topic, content_type="application/json", mode="command")
            descriptor = self.channels[topic]
            self._send(dict(descriptor, kind="advertise") if self._local_bridge else dict(kind="catalog", channels=list(self.channels.values())))

    def _command_done(self, future):
        with self._lock:
            self._executing.discard(future)

    def _command(self, packet, generation):
        if generation != self._generation or not self.is_connected:
            return
        ok = True
        try:
            with self._lock:
                handler = self._handlers.get(packet.topic)
            if handler is None:
                raise ValueError("No command handler registered on this host")
            result = handler(json.loads(packet.payload))
        except Exception as error:
            ok, result = False, {"error": str(error)}
        if generation == self._generation and self.is_connected:
            with contextlib.suppress(OSError, ValueError):
                self._send(dict(kind="response", reply_to=packet.header.get("id"), ok=ok), json.dumps(result, allow_nan=False).encode())

    def request(self, topic, value=None, timeout=5):
        """One acknowledged command; no retry or replay on link loss."""
        ident, waiter = str(uuid.uuid4()), queue.Queue(maxsize=1)
        with self._lock:
            self._pending[ident] = waiter
        try:
            self._send(dict(kind="request", topic=topic, id=ident), json.dumps(value or {}).encode())
            response = waiter.get(timeout=timeout)
            if isinstance(response, Exception):
                raise response
            if not response.header.get("ok", False):
                raise RuntimeError(response.payload.decode(errors="replace"))
            return json.loads(response.payload)
        except queue.Empty:
            raise TimeoutError("No USB command acknowledgement; command was not replayed")
        finally:
            with self._lock:
                self._pending.pop(ident, None)

    def receive(self, timeout=1):
        """Read a raw USBPacket from any active iPhone stream (timeout seconds)."""
        if self._packets is None:
            self._packets = queue.Queue(maxsize=128)
            def receive(packet):
                if isinstance(packet, Exception):
                    while not self._packets.empty():
                        with contextlib.suppress(queue.Empty):
                            self._packets.get_nowait()
                try:
                    self._packets.put_nowait(packet)
                except queue.Full:
                    raise BufferError("USB receive queue overflow; reconnecting to preserve packet ordering")
            with self._lock:
                self._callbacks["raw"] = receive
        try:
            packet = self._packets.get(timeout=timeout)
        except queue.Empty:
            return None
        if isinstance(packet, Exception):
            raise packet
        return packet

    def close(self):
        self._stop.set()
        sock = self._socket
        if sock:
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=6)
        self._executor.shutdown(wait=False)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


_SHARED = {}
_SHARED_LOCK = threading.Lock()


class USBPortReader:
    """Internal typed-receiver adapter; video stays ordered before decoding."""
    def __init__(self, host, port, hwm, conflate, family="stream"):
        self.key = host[4:] if host.startswith("usb:") else None
        self.queue = queue.Queue(maxsize=max(2, hwm))
        self.ident = str(uuid.uuid4())
        self.generation = 0
        self.last_error = None
        with _SHARED_LOCK:
            if self.key not in _SHARED:
                _SHARED[self.key] = [USBConnection(self.key), 0]
            self.session = _SHARED[self.key][0]
            _SHARED[self.key][1] += 1
        def receive(packet):
            if not isinstance(packet, Exception) and packet.topic != "iphone.{}.{}".format(family, port):
                return
            if self.queue.full() and (conflate or isinstance(packet, Exception)):
                while not self.queue.empty():
                    with contextlib.suppress(queue.Empty):
                        self.queue.get_nowait()
            self.queue.put_nowait(packet)
        with self.session._lock:
            self.session._callbacks[self.ident] = receive

    def read(self, timeout):
        try:
            packet = self.queue.get(timeout=None if timeout == -1 else timeout / 1000)
        except queue.Empty:
            return None
        if isinstance(packet, Exception):
            self.generation += 1
            self.last_error = str(packet)
            return None
        self.last_error = None
        return packet.payload

    def close(self):
        with self.session._lock:
            self.session._callbacks.pop(self.ident, None)
        with _SHARED_LOCK:
            entry = _SHARED.get(self.key)
            if not entry:
                return
            entry[1] -= 1
            if entry[1] <= 0:
                _SHARED.pop(self.key)
                self.session.close()
