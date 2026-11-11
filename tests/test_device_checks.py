import json
from pathlib import Path

import pytest

from asmagic import STREAMS, ARDataSubscriber, HandPoseDataSubscriber, IMUDataSubscriber, WatchIMUReceiver
from asmagic.cli import main, TEST_STREAMS, save_report
from asmagic.diagnostics import inspect_frame, run_stream_check, StreamTestResult
from asmagic.proto import hand_pose_pb2, phone_msg_pb2


def test_device_test_inventory_covers_all_streams_watch_and_second_claw(capsys):
    assert set(TEST_STREAMS) == set(STREAMS) | {"watch", "claw2"}
    assert main(["--list"]) == 0
    output = capsys.readouterr().out
    assert all(name in output for name in TEST_STREAMS)
    assert "HTTP" in output and "5401" in output


@pytest.mark.parametrize("name", list(STREAMS))
def test_inspection_accepts_each_known_protocol_without_treating_defaults_as_motion(name):
    cls = STREAMS[name].subscriber
    frame = cls.decode(cls._message_type().SerializeToString())
    result = inspect_frame(name, frame)
    assert not result.usable and not result.errors


def test_probe_distinguishes_open_socket_no_data_and_received_empty_frame(publisher):
    socket, connect = publisher
    sub = connect(HandPoseDataSubscriber)
    assert sub.is_connected
    absent = run_stream_check("hand", sub, duration=.02)
    assert absent.status == "no_data" and absent.frames == 0
    socket.send(hand_pose_pb2.HandPoseFrame(source_timestamp=1).SerializeToString())
    empty = run_stream_check("hand", sub, duration=1, count=1)
    assert empty.status == "empty_data" and empty.frames == 1
    message = hand_pose_pb2.HandPoseFrame(source_timestamp=2)
    message.left_hand.joints.add(name="wrist", x=0, y=0, confidence=.9)
    socket.send(message.SerializeToString())
    valid = run_stream_check("hand", sub, duration=1, count=1)
    assert valid.status == "received" and valid.usable_frames == 1
    assert valid.component_frames["left_hand"] == 1


def test_camera_probe_reports_image_decode_errors_instead_of_receipt_success(publisher):
    socket, connect = publisher
    sub = connect(ARDataSubscriber)
    message = phone_msg_pb2.Phone(timestamp=1, color_img=b"invalid-jpeg", local_pose=[0, 0, 0, 0, 0, 0, 1])
    socket.send(message.SerializeToString())
    result = run_stream_check("ar", sub, duration=1, count=1)
    assert result.frames == 1 and result.status == "errors"
    assert any("rgb" in error for error in result.errors)


def test_finite_probe_captures_decoder_failure(publisher):
    socket, connect = publisher
    sub = connect(IMUDataSubscriber)
    socket.send(b"\xff")
    result = run_stream_check("imu", sub, duration=.05)
    assert result.status == "errors" and result.errors


def test_watch_probe_counts_individual_samples_and_zero_motion():
    from asmagic.proto import watch_batch_msg_pb2
    with WatchIMUReceiver(port=0) as receiver:
        message = watch_batch_msg_pb2.WatchBatch(frame_count=2)
        for _ in range(2):
            message.frames.add(timestamp=1, attitude=[0, 0, 0, 1], rotation_rate=[0, 0, 0])
        receiver._enqueue(receiver.decode(message.SerializeToString()))
        result = run_stream_check("watch", receiver, duration=1, count=1)
        assert result.status == "received" and result.frames == 1 and result.samples == 2
        assert result.component_frames["rotation_rate"] == 1


def test_report_saves_skipped_and_unchecked_states_without_nonstandard_nan(tmp_path):
    target = tmp_path / "reports" / "device.json"
    results = [StreamTestResult("hand", "tcp://phone:8101", status="no_data"),
               StreamTestResult("watch", "", status="skipped", last_values={"missing": float("nan")})]
    save_report(target, results)
    data = json.loads(target.read_text())
    assert data["results"][0]["manual_observation"] == "not_checked"
    assert data["results"][1]["status"] == "skipped"
    assert data["results"][1]["last_values"]["missing"] is None


def test_cli_single_stream_receives_real_tcp_and_writes_report(publisher, monkeypatch, tmp_path):
    socket, connect = publisher

    def subscribe(name, ip, **options):
        assert name == "hand"
        sub = connect(HandPoseDataSubscriber)
        message = hand_pose_pb2.HandPoseFrame(source_timestamp=3)
        message.left_hand.joints.add(name="wrist", x=.2, y=.8, confidence=.9)
        socket.send(message.SerializeToString())
        return sub

    monkeypatch.setattr("asmagic.cli.subscribe", subscribe)
    report = tmp_path / "cli.json"
    assert main(["hand", "--ip", "127.0.0.1", "--count", "1", "--duration", "1", "--report", str(report)]) == 0
    result = json.loads(report.read_text())["results"][0]
    assert result["status"] == "received" and result["frames"] == 1
    assert result["last_values"]["left_hand_joints"] == 1


def test_guided_quit_marks_unexecuted_streams_in_report(monkeypatch, tmp_path):
    from types import SimpleNamespace
    choices = iter(["s", "q"])
    monkeypatch.setattr("asmagic.cli.sys.stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("builtins.input", lambda prompt: next(choices))
    report = tmp_path / "guided.json"
    assert main(["--all", "--ip", "phone", "--report", str(report)]) == 1
    results = json.loads(report.read_text())["results"]
    assert len(results) == len(TEST_STREAMS)
    assert results[0]["status"] == "skipped"
    assert all(item["status"] == "not_run" for item in results[1:])
