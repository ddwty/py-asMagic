# Changelog

## Unreleased

- Publish the SDK source at `ddwty/py-asMagic` with updated project links, English and Chinese quick starts, and contribution instructions.
- Add CI for regression tests, documentation consistency, package builds and wheel installation.
- Make documentation generation independent of external checkouts.
- Fix HEVC decoding with supported PyAV versions that omit the named low-delay codec flag.

## 1.0.2 — 2026-11-03

- Add `CameraDataSubscriber` on TCP 8105 and `CameraFrame` for ordinary-camera RGB, capture timestamps, dimensions and orientation.
- Reuse JPEG/HEVC decoding and background reception, including decoded-frame conflation and reference reset after camera or format changes.
- Add camera streaming to `subscribe()`, CLI diagnostics and runnable examples.

## 1.0.1 — 2026-10-21

- Add typed body and hand joints, multi-person body tracking, face landmarks and blendshapes, and tracking plots.
- Include camera, motion, controller, body, hand, face, AirPods, gripper and Watch receivers.
- Use `frame = sub.receive()` and direct AR/IMU field access. Remove AR/IMU `get()` and `get_*()` helpers; retain raw depth as `frame.depth` and pose matrices as `frame.local_pose_matrix` / `frame.global_pose_matrix`.
- Include plotting and HEVC dependencies in the default installation.

For changes affecting older applications, see the [compatibility guide](docs/compatibility.md).
