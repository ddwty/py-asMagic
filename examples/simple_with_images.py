"""Camera display entrypoint; shares the documented preview example."""
import argparse
from importlib import import_module

main = import_module("documentation.ar.03_display_images").main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip", nargs="?", default="192.168.1.100")
    main(parser.parse_args().ip)
