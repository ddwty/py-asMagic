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
