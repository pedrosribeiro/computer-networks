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

    while True:
        data, addr = sock.recvfrom(BUF_SIZE)

        if data == END_BYTE:
            print("End byte received. Ending transfer.")
            break

        recv_data += data

    if recv_data.startswith(b"BEGIN 200"):
        print("Server sent the file.")

        print(f"Data received: {recv_data}")

        header_length = len("BEGIN 200".encode(ENCODING))
        process_file_data(recv_data[header_length:])  # Ignore "BEGIN 200"
    elif recv_data.startswith(b"BEGIN 404"):
        print("Server responded with 404 not found")
    else:
        print("Server has not recognized the request")


def process_file_data(data: bytes) -> None:
    accumulated_data = b""

    for i in range(0, len(data), CHECKSUM_SIZE + BUF_SIZE):
        received_checksum = data[i : i + CHECKSUM_SIZE].decode(ENCODING)

        # Data block bounds
        data_block_start = i + CHECKSUM_SIZE
        data_block_end = data_block_start + BUF_SIZE

        # Get the block of data
        data_block = data[data_block_start:data_block_end]

        calculated_checksum = calculate_checksum(data_block)

        # Verify the checksum
        if received_checksum == calculated_checksum:
            print(f"Checksum is valid {received_checksum}. Saving data block.")
            accumulated_data += data_block
        else:
            print(
                f"Checksum mismatch! Received: {received_checksum}, Calculated: {calculated_checksum}"
            )
            continue

    # Save file after processing all the blocks
    save_file(accumulated_data)


def save_file(data: bytes) -> None:
    with open("received_file_encoded", "wb") as file:
        file.write(data)
        print("Encoded file has been saved successfully.")

    decoded_data = data.decode(ENCODING)
    with open("received_file_decoded", "w", encoding=ENCODING) as file:
        file.write(decoded_data)
        print("Decoded file has been saved successfully.")


if __name__ == "__main__":
    while True:
        msg = input()
        send_message(msg)
        receive_file(UDP_ADDR)
