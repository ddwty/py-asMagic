from asmagic import ARDataSubscriber

sub = ARDataSubscriber("192.168.1.100")
try:
    while True:
        data = sub.receive()
        print(data.timestamp)
except KeyboardInterrupt:
    pass
finally:
    sub.close()
