# iPhone IMU

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/imu-data-receiving-examples). See that chapter for setup, data formats and limitations.

## Read all available IMU sensors (Network)

Source: [imu/01_all_sensors.py](../../examples/documentation/imu/01_all_sensors.py)

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

## Read all available IMU sensors (USB)

Source: [imu/01_all_sensors_usb.py](../../examples/documentation/imu/01_all_sensors_usb.py)

```bash
python examples/documentation/imu/01_all_sensors_usb.py
```

```python
from asmagic import IMUDataSubscriber

# Receive from the USB-connected iPhone
sub = IMUDataSubscriber("usb")

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

## Read motion continuously (Network)

Source: [imu/02_quick_start.py](../../examples/documentation/imu/02_quick_start.py)

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

## Read motion continuously (USB)

Source: [imu/02_quick_start_usb.py](../../examples/documentation/imu/02_quick_start_usb.py)

```bash
python examples/documentation/imu/02_quick_start_usb.py
```

```python
from asmagic import IMUDataSubscriber

# Receive from the USB-connected iPhone
sub = IMUDataSubscriber("usb")

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
