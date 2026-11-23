"""Installed command: asmagic usb list|doctor|setup."""
import argparse
import json
import shlex
import shutil
import subprocess
import sys

from .usb_host import host_platform, setup_commands, usb_status


def _command_text(command):
    return subprocess.list2cmdline(command) if host_platform() == "Windows" else shlex.join(command)


def main(argv=None):
    parser = argparse.ArgumentParser(description="asMagic USB device discovery and host setup")
    groups = parser.add_subparsers(dest="group", required=True)
    usb = groups.add_parser("usb", help="USB iPhone connection")
    actions = usb.add_subparsers(dest="action", required=True)
    for action in ("list", "doctor"):
        command = actions.add_parser(action)
        command.add_argument("--json", action="store_true", help="Print machine-readable status")
    setup = actions.add_parser("setup", help="Install system USB support; may request administrator access")
    setup.add_argument("--print-only", action="store_true", help="Show system commands without running them")
    args = parser.parse_args(argv)
    if args.action == "setup":
        status = usb_status()
        try:
            needs_pair_tool = host_platform() == "Linux" and not shutil.which("idevicepair")
            commands = setup_commands() if not status["service_available"] or needs_pair_tool else []
            for command in commands:
                print(_command_text(command), flush=True)
                if not args.print_only:
                    subprocess.run(command, check=True)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            print(str(error), file=sys.stderr)
            return 1
        if args.print_only:
            if not commands:
                print(status["next_action"])
            return 0
        print("Reconnect iPhone, unlock it and trust this computer. Open asMagic in the foreground.")
        status = usb_status()
        # Pairing uses the OS trust UI or idevicepair; never bypass it.
        if status["service_available"] and len(status["devices"]) == 1 and shutil.which("idevicepair"):
            try:
                result = subprocess.run(["idevicepair", "-u", status["devices"][0]["udid"], "pair"])
                if result.returncode:
                    print("Finish the trust prompt, then retry asmagic usb setup.", file=sys.stderr)
                    return 1
            except OSError as error:
                print(str(error), file=sys.stderr)
                return 1
        elif len(status["devices"]) > 1:
            print("Several iPhones attached. Pair a selected device with idevicepair -u UDID pair.")
        if not status["service_available"]:
            print(status["error"], file=sys.stderr)
            print(status["next_action"], file=sys.stderr)
            return 1
        return 0
    status = usb_status()
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        print("USB service: " + ("available" if status["service_available"] else "unavailable"))
        for device in status["devices"]:
            print("{} | {} | {} | host=usb:{}".format(
                device.get("name") or "Unknown name", device.get("device_type") or "Apple device",
                device.get("product_type") or "Unknown model", device["udid"]))
            if device.get("identity_error"):
                print("  Identity: " + device["identity_error"])
        if status["error"]:
            print(status["error"])
        print(status["next_action"])
    return 0 if status["service_available"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
