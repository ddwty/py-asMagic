"""Compatibility import for the original AR-only package module."""
from .arDataSubscriber import ARDataSubscriber, connect, DEFAULT_PORT, DEFAULT_HWM, DEFAULT_TIMEOUT

__all__ = ["ARDataSubscriber", "connect"]
