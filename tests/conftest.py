import pytest
import zmq


@pytest.fixture
def publisher():
    context = zmq.Context()
    socket = context.socket(zmq.XPUB)
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt(zmq.XPUB_VERBOSE, 1)
    port = socket.bind_to_random_port("tcp://127.0.0.1")
    subscribers = []

    def connect(cls, **kwargs):
        sub = cls("127.0.0.1", port=port, **kwargs)
        subscribers.append(sub)
        # Wait for actual subscription propagation, avoiding a guessed sleep.
        assert socket.poll(2000, zmq.POLLIN), "subscription did not reach publisher"
        assert socket.recv()[0] == 1
        return sub

    yield socket, connect
    for sub in subscribers:
        sub.close()
    socket.close(0)
    context.term()
