import os
import socket
import threading

from config import SERVER_ADDR


def parse_request(request):
    try:
        headers = request.split("\n")
        filename = headers[0].split()[1]
        return filename if filename != "/" else "/index.html"
    except IndexError:
        return None


def get_file_content(filepath):
    if os.path.exists(filepath):
        with open(filepath, "rb") as file:
            content = file.read()

        if filepath.endswith(".html"):
            content_type = "text/html"
        elif filepath.endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        else:
            content_type = "application/octet-stream"
        return content, content_type

    # File not found
    content, content_type = get_file_content("storage/not_found.html")
    return content, "text/html"


def build_response(status, content_type, content, connection="keep-alive"):
    response_header = f"HTTP/1.1 {status}\r\n"
    response_header += f"Content-Type: {content_type}\r\n"
    response_header += f"Content-Length: {len(content)}\r\n"
    response_header += f"Connection: {connection}\r\n\r\n"
    return response_header.encode() + content


def handle_client_connection(client_socket):
    while True:
        try:
            request = client_socket.recv(4096).decode()
            if not request:
                break

            print(request)
            filename = parse_request(request)
            if not filename:
                break

            filepath = os.path.join("storage", filename.lstrip("/"))
            content, content_type = get_file_content(filepath)
            status = "200 OK" if os.path.exists(filepath) else "404 Not Found"
            response = build_response(status, content_type, content)
            client_socket.sendall(response)

        except Exception as e:
            print(f"Error handling client: {e}")
            break

    client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDR)
    server_socket.listen(5)
    print(f"Server running at {SERVER_ADDR}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client_connection, args=(client_socket,)
            )
            client_thread.start()
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
