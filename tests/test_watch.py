import http.client
import threading

import pytest
from asmagic import WatchIMUReceiver
from asmagic.proto import watch_batch_msg_pb2, watch_msg_pb2


def request(receiver, payload=None, method="POST", path="/imu"):
    connection = http.client.HTTPConnection("127.0.0.1", receiver.port, timeout=2)
    try:
        connection.request(method, path, body=payload)
        response = connection.getresponse()
        result = response.status, response.read()
        return result
    finally:
        connection.close()


def make_batch(timestamp=4, count=3):
    message = watch_batch_msg_pb2.WatchBatch(batch_timestamp=timestamp, frame_count=count)
    for index in range(count):
        message.frames.add(timestamp=timestamp + index*.01, attitude=[0, 0, 0, 1],
                           rotation_rate=[1, 2, 3], gravity=[0, 0, -1], acceleration=[0, 0, .1])
    return message.SerializeToString()


def test_batch_head_and_all_samples():
    with WatchIMUReceiver(port=0) as receiver:
        assert request(receiver, method="HEAD")[0] == 200
        assert request(receiver, make_batch())[0] == 200
        batch = receiver.get(1000)
        assert batch.frame_count == 3 and len(batch.frames) == 3
        assert batch.frames[2].timestamp == pytest.approx(4.02)
        assert batch.frames[0].gravity[2] == -1
        assert receiver.has_received_data and receiver.received_frames == 1
        assert receiver.get(0) is None
    receiver.close()
    assert receiver.get(0) is None
    with pytest.raises(StopIteration):
        next(receiver)


def test_http_keep_alive_two_posts_same_connection():
    with WatchIMUReceiver(port=0, conflate=False) as receiver:
        connection = http.client.HTTPConnection("127.0.0.1", receiver.port, timeout=2)
        try:
            for timestamp in [1, 2]:
                connection.request("POST", "/imu", body=make_batch(timestamp))
                response = connection.getresponse()
                assert response.status == 200
                response.read()
            assert receiver.get(1000).timestamp == 1
            assert receiver.get(1000).timestamp == 2
        finally:
            connection.close()


def test_conflation_drops_batches_without_truncating_samples():
    with WatchIMUReceiver(port=0) as receiver:
        request(receiver, make_batch(1))
        request(receiver, make_batch(2))
        batch = receiver.get(1000)
        assert batch.timestamp == 2 and len(batch.frames) == 3
        assert receiver.dropped_batches == 1


def test_bounded_queue_and_bad_payload_recovery():
    with WatchIMUReceiver(port=0, conflate=False, max_batches=2) as receiver:
        for timestamp in [1, 2, 3]:
            assert request(receiver, make_batch(timestamp))[0] == 200
        assert receiver.dropped_batches == 1
        assert receiver.get(0).timestamp == 2 and receiver.get(0).timestamp == 3
        assert request(receiver, b"\xff")[0] == 400
        assert receiver.last_error
        bad_count = watch_batch_msg_pb2.WatchBatch(frame_count=9)
        bad_count.frames.add(attitude=[0, 0, 0, 1])
        assert request(receiver, bad_count.SerializeToString())[0] == 400
        assert request(receiver, make_batch())[0] == 200
        assert receiver.last_error is None
        assert request(receiver, make_batch(), path="/wrong")[0] == 404


@pytest.mark.parametrize("mode", ["single", "legacy"])
def test_explicit_old_watch_modes(mode):
    with WatchIMUReceiver(port=0, payload_format=mode) as receiver:
        cls = watch_batch_msg_pb2.Watch if mode == "single" else watch_msg_pb2.Watch
        message = cls(attitude=[0, 0, 0, 1])
        if mode == "single":
            message.timestamp = 8
        assert request(receiver, message.SerializeToString())[0] == 200
        batch = receiver.get(1000)
        assert batch.frame_count == 1
        assert batch.frames[0].timestamp == (8 if mode == "single" else 0)


def test_close_wakes_blocking_get():
    receiver = WatchIMUReceiver(port=0)
    values = []
    thread = threading.Thread(target=lambda: values.append(receiver.get(-1)))
    thread.start()
    receiver.close()
    thread.join(timeout=2)
    assert not thread.is_alive() and values == [None]
