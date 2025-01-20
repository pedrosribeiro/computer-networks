import hashlib
import os
import socket

from config import SERVER_ADDR


def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            client_socket.connect(SERVER_ADDR)
            print("Connected to server")
            return client_socket
        except (socket.error, ValueError) as e:
            print(f"Error connecting to {SERVER_ADDR}: {e}. Try again...")


def send_client_id(client_socket):
    client_id = input("Enter your client ID: ")
    client_socket.sendall(client_id.encode("utf-8"))
    return client_id


def send_request(client_socket):
    request = input("Enter your request (Arquivo NOME.EXT, Chat, Sair): ")
    client_socket.sendall(request.encode("utf-8"))
    return request


def receive_file_data(client_socket, file_size):
    received_data = b""
    remaining_size = file_size
    while remaining_size > 0:
        chunk = client_socket.recv(min(4096, remaining_size))
        received_data += chunk
        remaining_size -= len(chunk)
    return received_data


def save_received_file(received_data, client_id, filename):
    client_dir = os.path.join("downloads", client_id)
    os.makedirs(client_dir, exist_ok=True)
    filepath = os.path.join(client_dir, filename)

    with open(filepath, "wb") as file:
        file.write(received_data)


def handle_file_response(client_socket, client_id):
    response = client_socket.recv(4096).decode("utf-8")
    lines = response.split("\n")

    if lines[0] == "Arquivo não encontrado":
        print("File not found")
        return

    filename = lines[0].split(": ")[1]
    file_size = int(lines[1].split(": ")[1])
    file_hash = lines[2].split(": ")[1]

    received_data = receive_file_data(client_socket, file_size)

    if hashlib.sha256(received_data).hexdigest() != file_hash:
        print("Error: File hash mismatch.")
        print(f"Hash received: {file_hash}")
        print(f"Hash calculated: {hashlib.sha256(received_data).hexdigest()}")
        return

    status = client_socket.recv(4096).decode("utf-8")

    save_received_file(received_data, client_id, filename)
    print(f"File {filename} received and saved.")


def main():
    client_socket = connect_to_server()

    try:
        client_id = send_client_id(client_socket)

        while True:
            request = send_request(client_socket)

            if request == "Sair":
                break
            elif request.startswith("Arquivo"):
                handle_file_response(client_socket, client_id)
            elif request.startswith("Chat"):
                pass

    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
