import socket

from config import BUF_SIZE, ENCODING, END_BYTE, UDP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send_message(msg: str) -> None:
    msg_enc = msg.encode(encoding=ENCODING)
    msg_len = len(msg_enc)

    for i in range(0, msg_len, BUF_SIZE):
        sock.sendto(msg_enc[i : i + BUF_SIZE], UDP_ADDR)

    sock.sendto(END_BYTE, UDP_ADDR)

    print(f"Message sent to server: {msg}")


if __name__ == "__main__":
    while True:
        msg = input()
        send_message(msg)
