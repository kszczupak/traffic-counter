import socket

from config import config


def start_server():
    with socket.socket() as server:
        server.bind(config['server_address'])
        server.listen(1)
        client, _ = server.accept()
        with client:
            segment_idx = 0
            while True:
                segment_file_path = config['video_segments']['path']/f"raw_{segment_idx}.h264"
                fetch_file_from_socket(client, segment_file_path)

            client.shutdown(socket.SHUT_RDWR)


def fetch_file_from_socket(client_socket, file_path, chunk_size=8*1024):
    """
    Fetches file from tcp socket assuming following data order:
    - first 15 bytes - file size in bytes (header)
    - # of bytes defined in header - actual file data
    """
    with open(file_path, "wb") as file:
        file_size_frame = client.recv(15)
        file_size = int(file_size_frame.decode())
        remaining_bytes = file_size
        receiving_file = True
        while receiving_file:
            if remaining_bytes > chunk_size:
                data = client_socket.recv(chunk_size)
                remaining_bytes -= chunk_size
            else:
                data = client_socket.recv(remaining_bytes)
                receiving_file = False

            file.write(data)


if __name__ == '__main__':
    start_server()
