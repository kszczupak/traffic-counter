import socket
from time import time, sleep
from pathlib import Path
from queue import Queue
from threading import Thread

import picamera

from config import config


def capture_and_send_segments_to_server():
    segments_queue = Queue()
    capturing_thread = Thread(target=capture_raw_video_segment, args=(segments_queue,))
    sending_thread = Thread(target=send_segments_to_server, args=(segments_queue,))
    capturing_thread.start()
    sending_thread.start()

    capturing_thread.join()
    sending_thread.join()


def send_segments_to_server(segments_queue: Queue):
    def wait_for_connection_with_server(client_socket):
        print(f"Waiting for connection with: {config['server_address']}")
        connected = False
        while not connected:
            try:
                client_socket.connect(config['server_address'])
                connected = True
            except ConnectionRefusedError:
                sleep(0.5)
                
        print("Connected to server")

    with socket.socket() as s:
        wait_for_connection_with_server(s)
        while True:
            segment = segments_queue.get()
            if segment == "FINISH":
                break

            send_file_to_socket(segment, s)

        s.shutdown(socket.SHUT_RDWR)


def capture_raw_video_segment(segments_queue: Queue):
    camera = picamera.PiCamera(resolution=(1280, 720))
    segment_paths = raw_segment_paths()
    first_segment_path = next(segment_paths)
    camera.start_recording(first_segment_path)
    camera.wait_recording(config['video_segments']['duration'])
    segments_queue.put(first_segment_path)

    for segment_path in segment_paths:
        camera.split_recording(segment_path)
        camera.wait_recording(config['video_segments']['duration'])
        segments_queue.put(segment_path)

    camera.stop_recording()


def raw_segment_paths():
    """
    Generator which returns paths of the raw segments. Currently segment names repeat after 10 segments, which means
    that only 10 last raw segments will be preserved.
    """
    while True:
        for i in range(10):
            segment_name = f"raw_{i}.h264"
            yield config['video_segments']['path']/segment_name


def send_file_to_socket(file_name, target_socket):
    """
    Sends given file over tcp socket using following data order:
    - first 15 bytes: file size in bytes (header)
    - # of bytes defined in header - actual file data
    """
    with open(file_name, "rb") as file_to_send:
        size_frame = f"{get_size(file_to_send):015}"
        target_socket.send(str.encode(size_frame))
        target_socket.sendfile(file_to_send)


def get_size(file_object):
    """
    Returns size in bytes of the provided file object
    """
    file_object.seek(0, 2)
    size = file_object.tell()
    return size


if __name__ == '__main__':
    capture_and_send_segments_to_server()
