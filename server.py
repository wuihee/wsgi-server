import socket
import sys
from io import BytesIO

from application import app


class WSGIServer:
    """
    Simple WSGI server which receives HTTP requests, forwards them to a Python
    application, and returns the response.
    """

    def __init__(self, host, port, application):
        """
        Initialize the WSGI serverl.

        Args:
            host (str): IP address of the host machine where the server will run.
            port (int): Port which the server is listening on for incoming connections.
            application (Callable): WSGI application to handle incoming HTTP requests.
        """
        self.host = host
        self.port = port
        self.application = application

        # Create a TCP/IP socket.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Allow the socket to reuse the address in case the server is restarted.
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to the specified host and port.
        self.server_socket.bind((self.host, self.port))

        # Set the server to listen for incoming connections. '1' specifies that
        # only one connection can be queued at a time.
        self.server_socket.listen(1)

        print(f"Serving HTTP on {self.host}:{self.port} ...")

    def serve_forever(self):
        """
        Continuously listen for and handle incoming HTTP connections.
        """
        while True:
            client_connection, _ = self.server_socket.accept()
            with client_connection:
                self.handle_request(client_connection)

    def handle_request(self, client_connection):
        """
        Handle an incoming HTTP request and send the appropriate response.

        Args:
            client_connection (socket): Socket object representing the
                                        connection to the client.
        """
        # Receive the HTTP request.
        request_data = client_connection.recv(1024)
        request_text = request_data.decode("utf-8")
        print(f"Request:\n{request_text}")

        # Parse the HTTP request.
        request_line = request_text.splitlines()[0]
        request_method, path, _ = request_line.split()

        # Create WSGI environ dictionary.
        environ = self.get_environ(request_method, path)

        # Start the response.
        response_body = self.application(environ, self.start_response)
        response = self.response_headers + b"".join(response_body)

        # Send the response back to the client.
        client_connection.sendall(response)

    def get_environ(self, request_method, path):
        """
        Returns the WSGI environ variable containing information about the
        current HTTP request.

        REQUEST_METHOD: HTTP method used. E.g. GET, POST, etc.
        PATH_INFO: URL request. E.g. /index.html, /about, etc.
        QUERY_STRING: The query string part of the URL. E.g. http://example.com/?name=John, where the query string is name=John.
        SERVER_NAME: The IP address of the server.
        SERVER_PORT: The port number on which the server is listening.
        wsgi.input: A file-like object (usually an instance of io.BytesIO) that the application can use to read the request body.
        wsgi.errors: A file-like object for the error output.
        wsgi.version: The version of the WSGI specification being used.
        wsgi.multithread: Whether the environment is running in a multithreaded environment.
        wsgi.multiprocess: Whether the environment is running in a multiprocess environment.
        wsgi.run_once: Whether the application is only meant to handle a single request in its lifetime.
        wsgi.url_scheme: The URL scheme used (typically http or https).

        Args:
            request_method (str): The HTTP method used for the request.
            path (str): The URL path that was requested.

        Returns:
            dict: The environ variable.
        """
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
        """
        Creates the HTTP response by setting the status and headers.

        This method is a WSGI-required callback that the WSGI application
        calls to initiate the HTTP response, which is sent back to the client.

        Args:
            status (str): HTTP status code.
            response_headers (list): List of tuples containing header names
                                     and values. E.g. [('Content-Type', 'text/plain')].
            exc_info (tuple, optional): Tuple containing exception information.
        """
        # Default server headers to include in every response.
        server_headers = [
            ("Date", "Mon, 23 May 2022 12:54:48 GMT"),
            ("Server", "WSGIServer 0.1"),
        ]
        self.response_headers = f"HTTP/1.1 {status}\r\n".encode("utf-8")

        # Add the server headers and headers provided by the WSGI application.
        for header in server_headers + response_headers:
            self.response_headers += f"{header[0]}: {header[1]}\r\n".encode("utf-8")

        # End the header section with a blank line.
        self.response_headers += b"\r\n"


if __name__ == "__main__":
    server = WSGIServer("127.0.0.1", 8000, app)
    server.serve_forever()
