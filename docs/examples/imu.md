# IMU Data Receiving Examples

iPhone acceleration, angular velocity and magnetic field.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Read all available IMU sensors

Acceleration: G. Angular velocity: rad/s. Magnetic field: μT.

Source: [imu/01_all_sensors.py](../../examples/documentation/imu/01_all_sensors.py)

Run from the SDK project directory:

```bash
python examples/documentation/imu/01_all_sensors.py
```

```python
from asmagic import IMUDataSubscriber

#Create subscriber with your iPhone's IP address
sub = IMUDataSubscriber("192.168.1.100")

try:
    # Continuous IMU data streaming
    while True:
        data = sub.receive()
        print(f"Timestamp: {data.timestamp}")
        print(f"Accelerometer (G): {data.accelerometer}")
        print(f"Gyroscope (rad/s): {data.gyroscope}")
        print(f"Magnetometer (μT): {data.magnetometer}")
        print(f"Gravity (G): {data.gravity}")
        print(f"User Acceleration (G): {data.user_acceleration}")
        print(f"Attitude (quat): {data.attitude}")

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    sub.close()
```

## Example 2: Original Quick Start IMU receiving example

IMU quick start using direct frame fields.

Source: [imu/02_quick_start.py](../../examples/documentation/imu/02_quick_start.py)

Run from the SDK project directory:

```bash
python examples/documentation/imu/02_quick_start.py
```

```python
from asmagic import IMUDataSubscriber

#Create subscriber with your iPhone's IP address
sub = IMUDataSubscriber("192.168.1.100")

try:
    # Continuous IMU data streaming
    for data in sub:
        print(f"Timestamp: {data.timestamp}")
        print(f"Accelerometer (G): {data.accelerometer}")
        print(f"Gyroscope (rad/s): {data.gyroscope}")
        print(f"Magnetometer (μT): {data.magnetometer}")
        print(f"Gravity (G): {data.gravity}")
        print(f"User Acceleration (G): {data.user_acceleration}")
        print(f"Attitude (quat): {data.attitude}")

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    sub.close()
```
