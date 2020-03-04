import socket
from lib.utils import ClosableQueue
from threading import Thread

import ffmpeg

from config import config


def main():
    server_queues = {
        'raw_segments': ClosableQueue(),
        'ready_segments': ClosableQueue(),
        'files_to_delete': ClosableQueue()
    }

    threads = [
        Thread(target=fetch_raw_segments, args=(server_queues,)),
        Thread(target=convert_to_mp4, args=(server_queues,)),
        Thread(target=cleanup_files, args=(server_queues,))
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
            for queue in server_queues.values():
                queue.close()

            # but continue to wait for all thread to be closed instead of finishing immediately
    print("All child threads finished")


def fetch_raw_segments(server_queues):
    print("Waiting for connection with pi-camera (client)...")
    with socket.socket() as server:
        server.bind(config['server_address'])
        server.listen(1)
        client, _ = server.accept()
        print("Connection established, serving...")
        with client:
            segment_idx = 0
            while True:
                try:
                    segment_file_path = config['video_segments']['path']/f"raw_{segment_idx}.h264"
                    fetch_file_from_socket(client, segment_file_path)

                    if server_queues['raw_segments'].closed:
                        # Other thread (possibly main) requested to end execution
                        break

                    server_queues['raw_segments'].put(segment_file_path)
                    segment_idx += 1
                except DroppedConnection as e:
                    print(e)

                    # Send close signal to other threads
                    for queue in server_queues.values():
                        queue.close()

                    break

            client.shutdown(socket.SHUT_RDWR)


def convert_to_mp4(server_queues):
    segment_idx = 0

    convert_flags = {
        'c:v': 'copy',  # Copy video codec without re-encoding (it's MUCH faster)
        'f': 'mp4',
        # movflags fragments mp4 file, so it can be played in browser using MSE
        'movflags': 'empty_moov+default_base_moof+frag_keyframe',
        'loglevel': 'error',  # Suppress terminal logging
        'y': None  # Overwrite output files without asking
    }

    for raw_segment in server_queues['raw_segments']:
        converted_segment_file = config['video_segments']['path']/f"segment_{segment_idx}.mp4"

        # Executed command:
        # ffmpeg -i "raw_1.h264" -c:v copy -f mp4 -movflags empty_moov+default_base_moof+frag_keyframe seg_1.mp4
        (
            ffmpeg
            .input(str(raw_segment))
            .output(str(converted_segment_file), **convert_flags)
            .run()
        )

        server_queues['ready_segments'].put(converted_segment_file)
        print(f"Segment ready: {converted_segment_file}")
        server_queues['files_to_delete'].put(raw_segment)

        segment_idx += 1


def cleanup_files(server_queues):
    for file_to_delete in server_queues['files_to_delete']:
        file_to_delete.unlink()


def fetch_file_from_socket(client_socket, file_path):
    """
    Fetches file from tcp socket assuming following data order:
    - first 15 bytes - file size in bytes (header)
    - # of bytes defined in header - actual file data
    """
    file_size_frame = read_fixed_nbr_of_bytes_from_socket(client_socket, 15)
    file_size = int(file_size_frame.decode())
    raw_data = read_fixed_nbr_of_bytes_from_socket(client_socket, file_size)

    with open(file_path, "wb") as file:
        file.write(raw_data)


class DroppedConnection(Exception):
    pass


def read_fixed_nbr_of_bytes_from_socket(client_socket, nbr_of_bytes_to_read):
    received_bytes = bytearray()

    while len(received_bytes) - nbr_of_bytes_to_read:
        chunk = client_socket.recv(nbr_of_bytes_to_read - len(received_bytes))

        if chunk == b'':
            raise DroppedConnection(f"Dropped socked connection with {client_socket.getpeername()}")

        received_bytes.extend(chunk)

    return received_bytes


if __name__ == '__main__':
    main()
