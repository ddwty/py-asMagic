"""Receive full native ARKit or MediaPipe body data through one human API."""
from typing import Optional, Union

from ._subscriber import Subscriber
from .body_tracking import BodyTrackingFrame, BodyTrackingModel
from .proto import armpose_msg_pb2, multi_person_pose_pb2


class BodyTrackingDataSubscriber(Subscriber[BodyTrackingFrame]):
    def __init__(self, ip: str, *, model: Union[BodyTrackingModel, str], port: Optional[int] = None,
                 hwm: int = 1, conflate: bool = True, verbose: bool = False) -> None:
        self.model = BodyTrackingModel(model)
        self._message_type = (armpose_msg_pb2.Armpose if self.model == BodyTrackingModel.ARKIT
                              else multi_person_pose_pb2.MultiPersonPoseFrame)
        if port is None:
            port = 8100 if self.model == BodyTrackingModel.ARKIT else 8104
        super().__init__(ip, port, hwm, conflate, verbose)

    def decode(self, payload: bytes) -> BodyTrackingFrame:
        """Decode with this receiver's configured model; no new frame is consumed."""
        return BodyTrackingFrame.from_bytes(payload, model=self.model)
