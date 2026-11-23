"""Discovery and setup contracts; system installers are never executed in tests."""
import json

import pytest

import asmagic
from asmagic import usb_cli, usb_host
from asmagic.usb import _daemon


def test_missing_service_reports_platform_setup_without_running_installers(monkeypatch):
    monkeypatch.setattr(usb_host, "host_platform", lambda: "Linux")
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("no USB service")
    monkeypatch.setattr("asmagic.usb.socket.create_connection", unavailable)
    with pytest.raises(ConnectionError, match="asmagic usb setup"):
        _daemon(("127.0.0.1", 27015))
    status = asmagic.usb_status(("127.0.0.1", 27015))
    assert not status["service_available"]
    assert status["devices"] == []
    assert "asmagic usb setup" in status["next_action"]


def test_linux_setup_uses_system_packages_and_sudo(monkeypatch):
    monkeypatch.setattr(usb_host, "host_platform", lambda: "Linux")
    monkeypatch.setattr(usb_host.shutil, "which", lambda name: "/bin/" + name if name in ("apt-get", "sudo", "systemctl") else None)
    monkeypatch.setattr(usb_host.os, "geteuid", lambda: 1000, raising=False)
    monkeypatch.setattr(usb_host.os.path, "isdir", lambda path: path == "/run/systemd/system")
    assert usb_host.setup_commands() == [
        ["sudo", "apt-get", "update"],
        ["sudo", "apt-get", "install", "-y", "usbmuxd", "libimobiledevice-utils"],
        ["sudo", "systemctl", "start", "usbmuxd"],
    ]


def test_windows_setup_uses_apple_driver_and_macos_needs_no_installer(monkeypatch):
    monkeypatch.setattr(usb_host, "host_platform", lambda: "Windows")
    monkeypatch.setattr(usb_host.shutil, "which", lambda name: name if name == "winget" else None)
    assert usb_host.setup_commands() == [["winget", "install", "--exact", "--name", "Apple Devices", "--source", "msstore"]]
    monkeypatch.setattr(usb_host, "host_platform", lambda: "Darwin")
    assert usb_host.setup_commands() == []


def test_discovery_cli_emits_machine_readable_status_without_opening_app(monkeypatch, capsys):
    monkeypatch.setattr("asmagic.usb.usb_devices", lambda address=None: [{"id": 7, "udid": "phone-1"}])
    assert usb_cli.main(["usb", "list", "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["devices"] == [{"id": 7, "udid": "phone-1"}]
    assert status["service_available"]
    assert "Stream" in status["next_action"]


def test_setup_preview_never_runs_commands(monkeypatch, capsys):
    monkeypatch.setattr(usb_cli, "usb_status", lambda: {"service_available": False})
    monkeypatch.setattr(usb_cli, "setup_commands", lambda: [["sudo", "apt-get", "install", "usbmuxd"]])
    def forbidden(*args, **kwargs):
        pytest.fail("print-only must not run an installer")
    monkeypatch.setattr(usb_cli.subprocess, "run", forbidden)
    assert usb_cli.main(["usb", "setup", "--print-only"]) == 0
    assert "usbmuxd" in capsys.readouterr().out


def test_setup_stops_after_installer_failure(monkeypatch):
    monkeypatch.setattr(usb_cli, "usb_status", lambda: {"service_available": False})
    monkeypatch.setattr(usb_cli, "setup_commands", lambda: [["installer"]])
    def failed(*args, **kwargs):
        raise usb_cli.subprocess.CalledProcessError(1, args[0])
    monkeypatch.setattr(usb_cli.subprocess, "run", failed)
    assert usb_cli.main(["usb", "setup"]) == 1
