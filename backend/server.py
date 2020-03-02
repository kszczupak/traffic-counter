import socket

from config import config


def start_server():
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
                    segment_idx += 1
                    print(f"Received file: {segment_file_path}")
                except DroppedConnection as e:
                    print(e)
                    break

            client.shutdown(socket.SHUT_RDWR)


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
    start_server()
