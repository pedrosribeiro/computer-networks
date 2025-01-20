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


def receive_request(client_socket):
    request = client_socket.recv(1024).decode("utf-8").strip()
    return request


def receive_client_id(client_socket, client_address):
    client_id = client_socket.recv(1024).decode("utf-8").strip()
    print(f"[{client_address}] Client '{client_id}' connected.")
    return client_id


def process_request(request, client_socket, client_address, client_id):
    print(f"[{client_id}] Request from client: {request}")
    if request == "Sair":
        print(f"[{client_id}] Client desconnected.")
    elif request.startswith("Arquivo"):
        pass
    elif request.startswith("Chat"):
        pass


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
