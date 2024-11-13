import hashlib
import os
import random
import socket

from config import BUF_SIZE, CHECKSUM_SIZE, ENCODING, END_BYTE, UDP_ADDR

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

received_blocks = {}
missing_blocks = []


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
    file_name = None
    file_checksum = None
    receiving_file = False

    while True:
        data, addr = sock.recvfrom(BUF_SIZE)

        if data == END_BYTE:
            print("End byte received. Ending transfer.")
            break

        # Detecta o início de uma resposta do servidor com BEGIN 200
        if data.startswith(b"BEGIN 200"):
            header_parts = data.decode(ENCODING).split()
            file_name = header_parts[2]
            file_checksum = header_parts[3]
            print(f"Receiving file: {file_name}, file checksum: {file_checksum}")
            receiving_file = True  # Inicia a recepção do arquivo
            continue

        # Dados do arquivo recebidos em binário
        if receiving_file:
            if False and random.random() < 0.01:
                print("Simulating packet loss on client side...")
                continue  # Ignora o pacote
            recv_data += data
        else:
            if data.startswith(b"BEGIN 404"):
                print("Server responded with 404 not found")
            else:
                print("Server has not recognized the request")

    if receiving_file:
        print(f"processing {recv_data}")
        process_file_data(recv_data, file_checksum, file_name)


def process_file_data(data: bytes, file_checksum: bytes, file_name: str) -> None:
    global received_blocks, missing_blocks
    received_blocks.clear()
    missing_blocks.clear()

    i = 0
    while i < len(data):
        header = data[i : i + 5].decode(ENCODING)
        if header.startswith("BLOCK"):
            # Extract block id
            i += 6  # len() of "BLOCK "
            block_id_end = data.find(b" ", i)
            block_id = int(data[i:block_id_end])
            i = block_id_end + 1

            # Extract block checksum
            block_checksum_end = i + CHECKSUM_SIZE
            received_checksum = data[i:block_checksum_end].decode(ENCODING)
            i = block_checksum_end + 1

            # Extract block data
            block_data = data[i : i + BUF_SIZE]
            i += BUF_SIZE

            # Verify the checksum
            calculated_checksum = calculate_checksum(block_data)
            if received_checksum == calculated_checksum:
                received_blocks[block_id] = block_data
            else:
                print(
                    f"Checksum mismatch in block {block_id}! Requesting retransmission. Rcv {received_checksum} Calc {calculated_checksum}"
                )
                missing_blocks.append((file_name, block_id))
        else:
            print(f"Unexpected data format: {header}")
            break

    request_missing_blocks(missing_blocks)

    # Verificar o checksum do arquivo inteiro
    verify_complete_file(file_checksum, file_name)


def verify_complete_file(expected_checksum: str, file_name: str):
    attempts = 5
    while attempts > 0:
        # Verify the file checksum
        accumulated_data = b"".join(received_blocks[i] for i in sorted(received_blocks))
        calculated_file_checksum = calculate_checksum(accumulated_data)

        if calculated_file_checksum == expected_checksum:
            print(f"File checksum calculated: {calculated_file_checksum}")
            save_file(accumulated_data, file_name, encoding=ENCODING)
            break
        else:
            print("File checksum mismatch! Requesting retransmission of all blocks.")
            request_all_blocks(file_name)
            attempts -= 1


def request_all_blocks(file_name: str):
    block_id = 0
    while True:
        retransmit_msg = f"RETRANSMIT {file_name} {block_id}"
        send_message(retransmit_msg)
        print(f"Requesting retransmission of block {block_id} from file {file_name}")

        # Receber o bloco retransmitido
        data = b""
        while True:
            partial_data, addr = sock.recvfrom(BUF_SIZE)
            if partial_data == END_BYTE:
                break
            data += partial_data

        # Processar o bloco retransmitido
        if data.decode(ENCODING).startswith("ERROR"):
            print(f"Error received for block {block_id}: {data.decode(ENCODING)}")
            break  # Sai quando receber a mensagem de erro, significando que o bloco está fora dos limites.

        process_retransmitted_block(data, block_id)

        block_id += 1  # Avança para o próximo bloco


def request_missing_blocks(missing_blocks: list[tuple[str, int]]):
    for file_name, block_id in missing_blocks:
        retransmit_msg = f"RETRANSMIT {file_name} {block_id}"
        send_message(retransmit_msg)
        print(f"Requesting retransmission of block {block_id} from file {file_name}")

        # Receive the retransmitted block
        data = b""
        while True:
            partial_data, addr = sock.recvfrom(BUF_SIZE)
            if partial_data == END_BYTE:
                break
            data += partial_data
        process_retransmitted_block(data, block_id)


def process_retransmitted_block(data: bytes, expected_block_id: int):
    if data.decode(ENCODING).startswith("BLOCK"):
        parts = data.split(b" ", 4)
        file_name = parts[1].decode(ENCODING)
        block_id = int(parts[2])
        received_checksum = parts[3].decode(ENCODING)

        # Extract data block - everything after the checksum index
        checksum_index = data.find(received_checksum.encode(ENCODING)) + CHECKSUM_SIZE
        block_data = data[checksum_index + 1 :]

        # Verify the checksum
        calculated_checksum = calculate_checksum(block_data)
        if block_id == expected_block_id and received_checksum == calculated_checksum:
            received_blocks[block_id] = block_data
            print(f"Block {block_id} from {file_name} received successfully.")
        else:
            print(f"Checksum error in retransmitted block {block_id} from {file_name}.")
    elif data.decode(ENCODING).startswith("ERROR"):
        print(data.decode(ENCODING))
    else:
        print("Unexpected data in retransmitted block.")


def save_file(data: bytes, file_name: str, encoding: str) -> None:
    with open(f"downloads/{file_name}", "wb") as file:
        file.write(data)
    print(f"File {file_name} saved.")


if __name__ == "__main__":
    print("Client started")
    while True:
        msg = input()
        send_message(msg)
        receive_file(UDP_ADDR)
