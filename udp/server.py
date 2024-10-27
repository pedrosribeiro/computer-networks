import hashlib
import os
import socket

from config import BUF_SIZE, ENCODING, END_BYTE, UDP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(UDP_ADDR)


def calculate_checksum(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def send_file(filename: str, addr: tuple, encoding: str = ENCODING) -> None:
    begin_msg = "BEGIN 200"
    send_message(begin_msg, addr, False, encoding)

    with open(filename, mode="rb") as file:
        while True:
            data = file.read(BUF_SIZE)
            if not data:
                break

            checksum = calculate_checksum(data)
            send_message(checksum, addr, False, encoding)

            send_message(data, addr, False, encoding)

    send_message(END_BYTE, addr, False, encoding)
    print(f"File {filename} sent to client. Transfer completed")


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
    decoded_msg = encoded_msg.decode(ENCODING)
    if decoded_msg.startswith("GET /"):
        filename = decoded_msg.split("/")[1]
        if os.path.isfile(filename):
            send_file(filename, addr, encoding)
        else:
            send_message("BEGIN 404", addr, True, encoding)
    else:
        print("Protocol not recognized! Message discarded.")


def start_server() -> None:
    recv_msg = b""

    while True:
        data, addr = sock.recvfrom(BUF_SIZE)

        if data == END_BYTE:
            print(f"Message received: {recv_msg.decode(encoding=ENCODING)}")
            handle_message(recv_msg, addr)
            recv_msg = b""
        else:
            recv_msg += data


if __name__ == "__main__":
    start_server()
