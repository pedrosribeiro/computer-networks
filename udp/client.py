import hashlib
import socket

from config import BUF_SIZE, CHECKSUM_SIZE, ENCODING, END_BYTE, UDP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def calculate_checksum(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def send_message(msg: str) -> None:
    msg_enc = msg.encode(encoding=ENCODING)
    msg_len = len(msg_enc)

    for i in range(0, msg_len, BUF_SIZE):
        sock.sendto(msg_enc[i : i + BUF_SIZE], UDP_ADDR)

    sock.sendto(END_BYTE, UDP_ADDR)

    print(f"Message sent to server: {msg}")


def receive_file(server_addr: tuple):
    recv_data = b""
    file_checksum = None

    while True:
        data, addr = sock.recvfrom(BUF_SIZE)

        if data == END_BYTE:
            print("End byte received. Ending transfer.")
            break

        recv_data += data

    if recv_data.startswith(b"BEGIN 200"):
        print("Server sent the file.")

        print(f"Data received: {recv_data}")

        header_length = len("BEGIN 200 ".encode(ENCODING))
        file_checksum = recv_data[header_length : header_length + CHECKSUM_SIZE].decode(
            ENCODING
        )

        print(f"File checksum received: {file_checksum}")

        process_file_data(
            recv_data[header_length + CHECKSUM_SIZE :], file_checksum
        )  # Ignore "BEGIN 200" and checksum
    elif recv_data.startswith(b"BEGIN 404"):
        print("Server responded with 404 not found")
    else:
        print("Server has not recognized the request")


def process_file_data(data: bytes, file_checksum: bytes) -> None:
    accumulated_data = b""
    missing_blocks = []

    i = 0
    while i < len(data):
        print(f"DEPURANDO {data[i : i + 5]}")
        if data[i : i + 5] == b"BLOCK":
            # Extract block id
            i += 6  # len() of "BLOCK "
            block_id_end = data.find(b" ", i)
            block_id = int(data[i:block_id_end])
            i = block_id_end + 1
            print(f"BLOCK ID: {block_id}")

            # Extract block checksum
            block_checksum_end = i + CHECKSUM_SIZE
            received_checksum = data[i:block_checksum_end].decode(ENCODING)
            i = block_checksum_end + 1
            print(f"CHECKSUM: {received_checksum}")

            # Extract block data
            block_data = data[i : i + BUF_SIZE]
            i += BUF_SIZE
            print(f"BLOCK DATA {block_data}")

            # Verify the checksum
            calculated_checksum = calculate_checksum(block_data)
            # Verify the checksum
            if received_checksum == calculated_checksum:
                print(f"Checksum is valid {received_checksum}. Saving data block.")
                accumulated_data += block_data
            else:
                print(
                    f"Checksum mismatch in block {block_id}! "
                    f"Received: {received_checksum}, Calculated: {calculated_checksum}"
                )
                missing_blocks.append(block_id)
        else:
            print("Unexpected data format")
            break

    # Verify the file checksum
    calculated_file_checksum = calculate_checksum(accumulated_data)
    if calculated_file_checksum == file_checksum:
        print(f"File checksum is valid {file_checksum}. Saving file.")
        save_file(accumulated_data, encoding=ENCODING)
    else:
        print(
            f"File checksum mismatch! Received: {file_checksum}, Calculated: {calculated_file_checksum}"
        )


def save_file(data: bytes, encoding: str) -> None:
    with open("received_file_encoded", "wb") as file:
        file.write(data)
        print("Encoded file has been saved successfully.")

    with open("received_file_decoded", "w", encoding=encoding, newline="") as file:
        file.write(data.decode(encoding))
        print("Decoded file has been saved successfully.")


if __name__ == "__main__":
    print("Client started")
    while True:
        msg = input()
        send_message(msg)
        receive_file(UDP_ADDR)
