"""Guided real-device stream checks: asmagic-test --all --ip PHONE_IP --plot."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import zmq

from .diagnostics import StreamTestResult, run_stream_check
from .joints import BodyCoordinateSpace
from .streams import STREAMS, subscribe
from .watchIMUReceiver import WatchIMUReceiver


GUIDANCE = {
    "camera": "Open Stream, choose Camera, then enable Send camera. Switch lenses and check the RGB image.",
    "ar": "打开 Stream 并开始发送相机/位姿；移动手机。检查 RGB、深度、位姿和内参。无深度设备可没有深度。Robot control 位姿也用此端口。",
    "airpods": "连接支持头部跟踪的 AirPods，打开对应功能并发送；转动头部，检查四元数变化。",
    "imu": "打开 iPhone IMU 并开始发送；转动和移动手机，检查各传感器向量。",
    "body_pose": "打开二维上半身跟踪并发送；让肩、肘、手腕进入画面，抬手检查骨架。",
    "joystick": "连接手柄或打开虚拟摇杆并发送；操作双摇杆、按钮和扳机，检查对应字段。",
    "ar_body": "打开 Body tracking 并开始发送；让完整身体进入后置相机，走动、抬手、屈膝检查三维骨架。",
    "hand": "在 Stream 开启手部发送，或在 Face and Hand Tracking 开启 Hand tracking 并点 Send hands；移动双手和手指。",
    "face": "打开 Face and Hand Tracking，开启 Face tracking 并点 Send face；张嘴、眨眼，检查面部点与动作系数。",
    "claw": "打开第一个夹爪的数据输出；调整夹爪命令，检查 angle 和可选的 motor 数据。",
    "claw2": "有第二个夹爪时打开其输出（默认 5401）；没有此功能可跳过。",
    "watch": "本步骤 Python 是 HTTP 服务端。启动后，在 Watch 填写这台计算机的局域网 IP 和端口，开始发送并移动手腕。",
}
TEST_STREAMS = tuple(STREAMS) + ("claw2", "watch")
STATUS_TEXT = {"received": "收到有效数据", "received_with_errors": "收到数据，同时存在错误",
               "empty_data": "收到帧，但未出现有效传感器/跟踪结果", "no_data": "没有收到帧",
               "errors": "数据或接收错误", "skipped": "已跳过", "not_run": "尚未测试"}


def _safe_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _safe_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe_json(item) for item in value]
    return value


def save_report(path, results):
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    content = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
               "meaning": "接收与字段检查；设备识别准确率及动作对应关系需人工观察确认。未执行的通道不代表通过。",
               "results": [asdict(result) for result in results]}
    target.write_text(json.dumps(_safe_json(content), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="逐个连接 App 数据流，检查字段，按需绘图并保存 JSON 报告。")
    parser.add_argument("stream", nargs="?", choices=TEST_STREAMS, help="单项测试的数据流名称")
    parser.add_argument("--all", action="store_true", help="按顺序提示打开各功能；Enter 开始，s 跳过，q 退出")
    parser.add_argument("--list", action="store_true", help="列出测试名称、端口和 App 操作")
    parser.add_argument("--ip", help="发送数据的 iPhone IP（Watch 单项测试无需此参数）")
    parser.add_argument("--port", type=int, help="覆盖单项测试端口")
    parser.add_argument("--bind", default="0.0.0.0", help="Watch HTTP 监听地址，默认允许局域网连接")
    parser.add_argument("--watch-port", type=int, default=8002)
    parser.add_argument("--duration", type=float, default=15, help="每项接收时长，秒，默认 15")
    parser.add_argument("--count", type=int, default=0, help="收到指定帧数后提前结束；0 按时长测试")
    parser.add_argument("--plot", action="store_true", help="开启人体/手部/面部跟踪绘图，默认关闭")
    parser.add_argument("--images", action="store_true", help="相机通道显示 RGB 和深度窗口")
    parser.add_argument("--space", choices=("body", "world"), default="body", help="三维人体绘图坐标")
    parser.add_argument("--report", default="reports/app-streams.json", help="JSON 报告保存位置")
    args = parser.parse_args(argv)
    if args.list:
        for name in TEST_STREAMS:
            port = STREAMS[name].port if name in STREAMS else (5401 if name == "claw2" else args.watch_port)
            print("{} | {} {} | {}".format(name, "HTTP" if name == "watch" else "TCP", port, GUIDANCE[name]))
        return 0
    if args.all == bool(args.stream):
        parser.error("请指定一个 stream，或使用 --all；可先使用 --list")
    if (args.all or args.stream != "watch") and not args.ip:
        parser.error("ZeroMQ 测试需要 --ip，填写发送 iPhone 的地址")
    if args.all and args.port is not None:
        parser.error("--port 只用于单项测试；Watch 在全量测试中用 --watch-port")
    if not math.isfinite(args.duration) or args.duration <= 0 or args.count < 0:
        parser.error("--duration 必须大于零，--count 不能小于零")
    if args.all and not sys.stdin.isatty():
        parser.error("--all 需要交互终端，以便逐项切换 App 功能；脚本环境请逐个指定 stream")
    if args.plot:
        from .plotting import _pyplot
        try:
            _pyplot()
        except ImportError as error:
            parser.error(str(error))
    results = []
    selected = TEST_STREAMS if args.all else (args.stream,)
    for index, name in enumerate(selected):
        print("\n{}：{}".format(name, GUIDANCE[name]))
        if args.all:
            try:
                choice = input("Enter 开始 / s 跳过 / q 结束：").strip().lower()
            except (KeyboardInterrupt, EOFError):
                results.extend(StreamTestResult(item, "", status="not_run") for item in selected[index:])
                break
            if choice == "q":
                results.extend(StreamTestResult(item, "", status="not_run") for item in selected[index:])
                break
            if choice == "s":
                results.append(StreamTestResult(name, "", status="skipped"))
                save_report(args.report, results)
                continue
        receiver = None
        try:
            if name == "watch":
                receiver = WatchIMUReceiver(args.bind, args.port if args.port is not None else args.watch_port, conflate=False)
            else:
                options = {"port": args.port} if args.port is not None else ({"port": 5401} if name == "claw2" else {})
                receiver = subscribe("claw" if name == "claw2" else name, args.ip, **options)
            print("接收地址：", receiver.address)
            if name == "watch":
                print("服务已启动：请在 Watch 配置这台计算机的 IP 和端口", receiver.port)
            result = run_stream_check(name, receiver, duration=args.duration, count=args.count, plot=args.plot,
                                      plot_options={"space": BodyCoordinateSpace(args.space)}, images=args.images,
                                      on_status=lambda r: print("已收到 {} 帧，{} 帧有效；当前字段：{}".format(
                                          r.frames, r.usable_frames, json.dumps(_safe_json(r.last_values), ensure_ascii=False))))
        except (ValueError, RuntimeError, ImportError, OSError, zmq.ZMQError) as error:
            result = StreamTestResult(name, "", status="errors", errors=[str(error)])
        finally:
            if receiver is not None:
                receiver.close()
        print("结果：{}；{} 帧；接收速率 {:.1f} 帧/秒".format(STATUS_TEXT[result.status], result.frames, result.received_fps))
        if result.frames:
            print("最后一帧字段：", json.dumps(_safe_json(result.last_values), ensure_ascii=False))
        if result.errors:
            print("错误：", "; ".join(result.errors))
        if result.status in ("no_data", "empty_data"):
            print("检查对应功能是否开始发送、IP/端口、本地网络权限与防火墙；跟踪通道还需目标进入画面。")
        if args.all and result.frames and result.manual_observation != "interrupted":
            try:
                observed = input("动作与数值/绘图是否对应？y 是 / n 否 / Enter 尚未确认：").strip().lower()
                result.manual_observation = {"y": "matches", "n": "does_not_match"}.get(observed, "not_checked")
            except (KeyboardInterrupt, EOFError):
                result.manual_observation = "interrupted"
        results.append(result)
        save_report(args.report, results)
        if result.manual_observation == "interrupted":
            results.extend(StreamTestResult(item, "", status="not_run") for item in selected[index + 1:])
            break
    save_report(args.report, results)
    print("\n报告已保存：", str(Path(args.report).resolve()))
    return 1 if any(result.status not in ("received", "skipped") or result.manual_observation == "does_not_match" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
