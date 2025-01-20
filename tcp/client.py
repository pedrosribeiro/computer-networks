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


def main():
    client_socket = connect_to_server()

    try:
        client_id = send_client_id(client_socket)

        while True:
            request = send_request(client_socket)

            if request == "Sair":
                break
            elif request.startswith("Arquivo"):
                pass
            elif request.startswith("Chat"):
                pass

    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
