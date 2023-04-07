import threading
import time
import io
from serial import Serial


class DummySerial(Serial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = io.BytesIO()
        self.lock = threading.Lock()
        self.last_received_message = b''

    def read(self, size=1):
        with self.lock:
            self.buffer.seek(0)
            data = self.buffer.read(size)
            self.buffer.seek(0, io.SEEK_END)
            return data

    def write(self, data):
        with self.lock:
            self.buffer.write(data)

            self.last_received_message = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Perform any cleanup tasks here
        pass

    def isOpen(self):
        return True

    def read_all(self):
        with self.lock:
            return self.last_received_message


class VirtualSerialDeviceThread(threading.Thread):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            data = self.port.read()
            if data:
                self.port.write(b"ACK")
            time.sleep(0.1)

    def stop(self):
        self.stop_event.set()


if __name__ == "__main__":
    with DummySerial() as dummy_serial_port:
        virtual_device_thread = VirtualSerialDeviceThread(dummy_serial_port)
        virtual_device_thread.daemon = True
        virtual_device_thread.start()

        # Test the virtual device
        dummy_serial_port.write(b"Hello, Virtual Device!")
        time.sleep(2)  # Give the virtual device thread some time to process and write the response
        response = dummy_serial_port.read_all()
        print("Response from Virtual Device:", response)

        # Stop the virtual device thread
        virtual_device_thread.stop()
