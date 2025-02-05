import hashlib
import os
import socket
import threading

from config import SERVER_ADDR


def handle_client(client_socket, client_address):
    try:
        client_id = receive_client_id(client_socket, client_address)
        while True:
            request = receive_request(client_socket)
            if not request:
                break
            process_request(request, client_socket, client_address, client_id)
    finally:
        print(f"[{client_address}] Connection closed")
        client_socket.close()


def receive_client_id(client_socket, client_address):
    client_id = client_socket.recv(1024).decode("utf-8").strip()
    print(f"[{client_address}] Client '{client_id}' connected.")
    return client_id


def receive_request(client_socket):
    request = client_socket.recv(1024).decode("utf-8").strip()
    return request


def process_request(request, client_socket, client_address, client_id):
    print(f"[{client_id}] Request from client: {request}")
    if request == "Sair":
        print(f"[{client_id}] Client desconnected.")
    elif request.startswith("Arquivo"):
        handle_file_request(request, client_socket, client_id)
    elif request.startswith("Chat"):
        handle_chat(client_socket, client_id)


def handle_file_request(request, client_socket, client_id):
    filename = request.split()[1]
    filepath = os.path.join("storage", filename)

    if not os.path.isfile(filepath):
        send_message(client_socket, f"Arquivo não encontrado")
        print(f"[{client_id}] File '{filename}' requested not found")
        return

    send_file_header(client_socket, filepath)
    send_file_content(client_socket, filepath)
    print(f"[{client_id}] File '{filename}' sent to client successfully.")


def send_file_header(client_socket, filepath):
    file_size = os.path.getsize(filepath)
    file_hash = calculate_file_hash(filepath)

    header = f"Nome: {os.path.basename(filepath)}\nTamanho: {file_size}\nHash: {file_hash}\n".encode(
        "utf-8"
    )
    client_socket.sendall(header)


def calculate_file_hash(filepath):
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as file:
        while chunk := file.read(4096):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def send_file_content(client_socket, filepath):
    with open(filepath, "rb") as file:
        while chunk := file.read(4096):
            client_socket.sendall(chunk)
    send_message(client_socket, "\nStatus: ok")


def send_message(client_socket, message):
    client_socket.sendall(message.encode("utf-8"))


def handle_chat(client_socket, client_id):
    print(f"[{client_id}] Chat started.")
    while True:
        message = receive_request(client_socket)
        if not message or message == "Sair":
            print(f"[{client_id}] Chat ended.")
            break
        print(f"[{client_id}]: {message}")
        response = input(f"[You]: ")
        send_message(client_socket, response)


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDR)
    server_socket.listen(5)
    print("Server started...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            client_handler = threading.Thread(
                target=handle_client, args=(client_socket, client_address)
            )
            client_handler.start()
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
