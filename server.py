import socket
import sys
from io import BytesIO

from application import app


class WSGIServer:
    def __init__(self, host, port, application):
        self.host = host
        self.port = port
        self.application = application
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"Serving HTTP on {self.host}:{self.port} ...")

    def serve_forever(self):
        while True:
            client_connection, client_address = self.server_socket.accept()
            self.handle_request(client_connection)
            client_connection.close()  # ! Use context manager.

    def handle_request(self, client_connection):
        request_data = client_connection.recv(1024)
        request_text = request_data.decode("utf-8")
        print(f"Request:\n{request_text}")

        # Parse the HTTP request.
        request_line = request_text.splitlines()[0]  # ! What is .splitlines
        request_method, path, _ = request_line.split()

        # Create WSGI environ dictionary.
        environ = self.get_environ(request_method, path)

        # Start the response.
        response_body = self.application(environ, self.start_response)
        response = self.response_headers + b"".join(response_body)

        # Send the response back to the client.
        client_connection.sendall(response)

    def get_environ(self, request_method, path):
        return {
            "REQUEST_METHOD": request_method,
            "PATH_INFO": path,
            "SERVER_NAME": self.host,
            "SERVER_PORT": str(self.port),
            "wsgi.input": BytesIO(),
            "wsgi.errors": sys.stderr,
            "wsgi.version": (1, 0),
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "wsgi.url_scheme": "http",
        }

    def start_response(self, status, response_headers, exc_info=None):
        server_headers = [
            ("Date", "Mon"),
            ("Server", "WSGIServer 0.1"),  # ! Replace with datetime.
        ]
        self.response_headers = f"HTTP/1.1 {status}\r\n".encode("utf-8")
        for header in server_headers + response_headers:
            self.response_headers += f"{header[0]}: {header[1]}\r\n".encode("utf-8")
        self.response_headers += b"\r\n"


if __name__ == "__main__":
    server = WSGIServer("127.0.0.1", 8000, app)
    server.serve_forever()
