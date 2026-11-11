"""Receive any explicitly selected protobuf schema; never guess packet types."""
from google.protobuf.message import Message
from ._subscriber import Subscriber
from .proto import magiclaw_msg_pb2, watch_msg_pb2
from .decoders import watch_frame


class ProtobufSubscriber(Subscriber[Message]):
    def __init__(self, ip: str, port: int, message_type, hwm: int = 1,
                 conflate: bool = True, verbose: bool = False) -> None:
        if not isinstance(message_type, type) or not issubclass(message_type, Message):
            raise TypeError("message_type must be a generated protobuf Message class")
        self._message_type = message_type
        super().__init__(ip, port, hwm, conflate, verbose)

    def decode(self, payload: bytes) -> Message:
        message = self._message_type()
        message.ParseFromString(payload)
        return message


class MagiClawDataSubscriber(Subscriber[Message]):
    """Legacy combined message; a port is required because no app port is assigned."""
    _message_type = magiclaw_msg_pb2.MagiClaw


class LegacyWatchDataSubscriber(Subscriber):
    """Legacy ZeroMQ Watch.Watch message; current Watch uses WatchIMUReceiver."""
    _message_type = watch_msg_pb2.Watch
    _from_message = staticmethod(watch_frame)
