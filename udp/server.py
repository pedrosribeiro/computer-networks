import os
import socket

from config import BUF_SIZE, ENCODING, END_BYTE, UDP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(UDP_ADDR)


def handle_message(encoded_msg: bytes) -> None:
    decoded_msg = encoded_msg.decode(ENCODING)
    if decoded_msg.startswith("GET /"):
        filename = decoded_msg.split("/")[1]
        if os.path.isfile(filename):
            print(f"{filename} FOUND!")
            pass
        else:
            print(f"{filename} NOT FOUND!")
            pass
    else:
        print("Protocol not recognized! Message discarded.")


def start_server() -> None:
    recv_msg = b""

    while True:
        data, addr = sock.recvfrom(BUF_SIZE)

        if data == END_BYTE:
            print(f"Message received: {recv_msg.decode(encoding=ENCODING)}")
            handle_message(recv_msg)
            recv_msg = b""
        else:
            recv_msg += data


if __name__ == "__main__":
    start_server()
