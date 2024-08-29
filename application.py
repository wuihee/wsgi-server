def app(environ, start_response):
    """
    A simple WSGI application that returns 'Hello, World!'.
    """
    status = "200 OK"
    headers = [("Content-Type", "text/plain")]
    start_response(status, headers)
    return [b"Hello, World!"]
