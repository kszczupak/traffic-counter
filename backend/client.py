import socket
from time import time, sleep
from pathlib import Path
from lib.utils import ClosableQueue, get_cpu_temperature
from threading import Thread
from subprocess import check_output

import picamera

from config import config, project_root


def capture_and_send_segments_to_server():
    segments_queue = ClosableQueue()

    threads = [
        Thread(target=capture_raw_video_segment, args=(segments_queue,)),
        Thread(target=send_segments_to_server, args=(segments_queue,))
    ]

    for thread in threads:
        thread.start()

    # wait for thread completion
    for thread in threads:
        try:
            thread.join()
        except KeyboardInterrupt:
            print("User initiated termination, closing all child threads...")
            # request to close all child threads
            segments_queue.close()
            # but continue to wait for all thread to be closed instead of finishing immediately

    print("All child threads finished")


def send_segments_to_server(segments_queue: ClosableQueue):
    def wait_for_connection_with_server(client_socket):
        print(f"Waiting for connection with: {config['server_address']}")
        connected = False
        while not connected:
            try:
                client_socket.connect(config['server_address'])
                connected = True
            except ConnectionRefusedError:
                sleep(0.5)

        print("Connected to server; capturing and sending video segments...")

    with socket.socket() as s:
        wait_for_connection_with_server(s)
        segments_queue.put("CONNECTION_ESTABLISHED")
        wait_for_message(segments_queue, "CAMERA_INITIALIZED")

        for segment in segments_queue:
            print(f"Sending file: {segment}", end=" ")

            try:
                send_file_to_socket(segment, s)
            except BrokenPipeError:
                print()
                print("Lost connection with the server")

                # Signal to finish the main function and therefore all started threads (working as daemons)
                segments_queue.close()
                return

            print("| Completed")

        s.shutdown(socket.SHUT_RDWR)


def wait_for_message(queue: ClosableQueue, message):
    """
    Waits until given message will appear at the front of the queue.
    This is a blocking operation.
    """
    if queue.closed:
        return

    print(f"Waiting for message: {message}")
    for current_message in queue:
        if current_message == message:
            print(f"Received message: {message}")
            break


def capture_raw_video_segment(segments_queue: ClosableQueue):
    wait_for_message(segments_queue, "CONNECTION_ESTABLISHED")

    with picamera.PiCamera(resolution=(1280, 720)) as camera:
        segments_queue.put("CAMERA_INITIALIZED")

        segment_paths = raw_segment_paths()
        first_segment_path = next(segment_paths)
        camera.start_recording(first_segment_path)
        camera.wait_recording(config['video_segments']['duration'])

        previous_segment_path = first_segment_path

        for next_segment_path in segment_paths:
            camera.split_recording(next_segment_path)

            if segments_queue.closed:
                # other thread requested to end work
                break

            segments_queue.put(previous_segment_path)

            camera.wait_recording(config['video_segments']['duration'])
            previous_segment_path = next_segment_path

        camera.stop_recording()


def raw_segment_paths():
    """
    Generator which returns paths of the raw segments. Currently segment names repeat after 10 segments, which means
    that only 10 last raw segments will be preserved.
    """
    while True:
        for i in range(10):
            segment_name = f"raw_{i}.h264"
            yield str(config['video_segments']['path']/segment_name)


def send_file_to_socket(file_name, target_socket):
    """
    Sends given file over tcp socket using following data order:
    - first 15 bytes: file size in bytes (header)
    - # of bytes defined in header - actual file data
    """
    with open(file_name, "rb") as file_to_send:
        size_frame = f"{get_size(file_to_send):015}"
        target_socket.sendall(str.encode(size_frame))
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
