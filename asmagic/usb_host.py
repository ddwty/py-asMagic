"""USB host diagnostics and explicit system setup, shared by API and CLI."""
import os
import platform
import shutil


def host_platform():
    return platform.system()


def setup_hint():
    system = host_platform()
    if system == "Windows":
        return "Install Apple Devices and start Apple Mobile Device Service: asmagic usb setup"
    if system == "Linux":
        return "Install/start usbmuxd: asmagic usb setup"
    if system == "Darwin":
        return "macOS supplies the USB service. Reconnect iPhone, unlock and trust this Mac; run asmagic usb doctor"
    return "Install the host's Apple/usbmuxd USB service; run asmagic usb doctor"


def setup_commands():
    """Return argument lists; setup runs these only on explicit CLI invocation."""
    system = host_platform()
    if system == "Windows":
        if not shutil.which("winget"):
            raise RuntimeError("Install Apple Devices from Microsoft Store, then reconnect iPhone.")
        return [["winget", "install", "--exact", "--name", "Apple Devices", "--source", "msstore"]]
    if system == "Darwin":
        return []
    if system != "Linux":
        raise RuntimeError("Install usbmuxd and libimobiledevice with your system package manager.")
    if shutil.which("apt-get"):
        commands = [["apt-get", "update"],
                    ["apt-get", "install", "-y", "usbmuxd", "libimobiledevice-utils"]]
    elif shutil.which("dnf"):
        commands = [["dnf", "install", "-y", "usbmuxd", "libimobiledevice-utils"]]
    elif shutil.which("pacman"):
        commands = [["pacman", "-S", "--needed", "--noconfirm", "usbmuxd", "libimobiledevice"]]
    else:
        raise RuntimeError("Install usbmuxd and libimobiledevice with your system package manager.")
    if shutil.which("systemctl") and os.path.isdir("/run/systemd/system"):
        commands.append(["systemctl", "start", "usbmuxd"])
    if os.geteuid() != 0:
        if not shutil.which("sudo"):
            raise RuntimeError("Run asmagic usb setup as root to install system USB support.")
        commands = [["sudo"] + command for command in commands]
    return commands


def usb_status(address=None):
    """Inspect the USB service and devices without taking an app session.

    Enumeration confirms attachment. Open asMagic and start a Stream to receive
    data; a listed device alone does not establish app readiness.
    """
    from .usb import usb_devices
    result = dict(platform=host_platform(), service_available=False, devices=[],
                  error=None, next_action=None)
    try:
        result["devices"] = usb_devices(address)
        result["service_available"] = True
        result["next_action"] = ("Open asMagic in the foreground and start a Stream."
                                 if result["devices"] else
                                 "Connect iPhone with a data cable, unlock it and trust this computer.")
    except (OSError, ValueError) as error:
        result["error"] = str(error)
        result["next_action"] = setup_hint()
    return result
