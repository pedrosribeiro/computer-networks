import hashlib
import os
import random
import socket

from config import BUF_SIZE, ENCODING, END_BYTE, STORAGE_PATH, UDP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(UDP_ADDR)
sock.settimeout(10)


def calculate_checksum(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def send_file(filename: str, addr: tuple, encoding: str = ENCODING) -> None:

    with open(os.path.join(STORAGE_PATH, filename), mode="rb") as file:

        file_checksum = calculate_checksum(file.read())
        file.seek(0)  # Reset file pointer to the beginning

        begin_msg = f"BEGIN 200 {filename} {file_checksum}"
        send_message(begin_msg, addr, False, encoding)

        block_id = 0

        # Loop to send the file
        while True:
            data = file.read(BUF_SIZE)
            if not data:
                break

            checksum = calculate_checksum(data)
            block_msg = f"BLOCK {block_id} {checksum} ".encode(encoding) + data

            if random.random() < 0.1:
                print("Simulating packet loss on server side...")
                continue

            send_message(block_msg, addr, False, encoding)

            block_id += 1

    send_message(END_BYTE, addr, False, encoding)
    print(f"File {filename} sent to client. Transfer completed")


def send_block(
    filename: str, block_id: int, addr: tuple, encoding: str = ENCODING
) -> None:
    with open(os.path.join(STORAGE_PATH, filename), mode="rb") as file:
        # Move cursor to the beginning of the specific block
        file.seek(block_id * BUF_SIZE)
        data = file.read(BUF_SIZE)

        if not data:
            print(f"Block {block_id} is out of range for file {filename}.")
            send_message(
                f"ERROR {filename} Block {block_id} out of range", addr, True, encoding
            )
            return

        checksum = calculate_checksum(data)
        block_msg = f"BLOCK {filename} {block_id} {checksum} ".encode(encoding) + data

        send_message(block_msg, addr, True, encoding)

    print(f"Retransmitted block {block_id} for file {filename} to client.")


def send_message(
    msg: str | bytes,
    addr: tuple,
    end_byte: bool = True,
    encoding: str = ENCODING,
) -> None:
    if isinstance(msg, str):
        msg_enc = msg.encode(encoding=encoding)
    else:
        msg_enc = msg
    msg_enc_len = len(msg_enc)

    for i in range(0, msg_enc_len, BUF_SIZE):
        sock.sendto(msg_enc[i : i + BUF_SIZE], addr)

    if end_byte:
        sock.sendto(END_BYTE, addr)

    print(f"Message sent to client: {msg}")


def handle_message(encoded_msg: bytes, addr: tuple, encoding: str = ENCODING) -> None:
    if encoded_msg.startswith(b"GET /"):  # GET /{file_name}
        decoded_msg = encoded_msg.decode(encoding)
        filename = decoded_msg.split("/")[1]
        if os.path.isfile(os.path.join(STORAGE_PATH, filename)):
            send_file(filename, addr, encoding)
        else:
            send_message("BEGIN 404", addr, True, encoding)
    elif encoded_msg.startswith(b"RETRANSMIT"):  # RETRANSMIT {file_name} {block_id}
        decoded_msg = encoded_msg.decode(encoding)
        parts = decoded_msg.split()
        filename = parts[1]
        block_id = int(parts[2])
        if os.path.isfile(os.path.join(STORAGE_PATH, filename)):
            send_block(filename, block_id, addr, encoding)
        else:
            send_message("BEGIN 404", addr, True, encoding)
    else:
        send_message("BEGIN 400", addr, True, encoding)
        print("Protocol not recognized! Message discarded.")


def start_server() -> None:
    recv_msg = b""

    while True:
        try:
            data, addr = sock.recvfrom(BUF_SIZE)

            if data == END_BYTE:
                print(f"Message received: {recv_msg.decode(encoding=ENCODING)}")
                handle_message(recv_msg, addr)
                recv_msg = b""
            else:
                recv_msg += data
        except socket.timeout:
            print("...")


if __name__ == "__main__":
    print("Server started")
    start_server()
