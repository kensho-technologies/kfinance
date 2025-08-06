from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from threading import Thread


refresh_token: str | None = None


class ServerThread(Thread):
    def __init__(self, daemon: bool = True) -> None:
        """Construct a thread to hold an HTTPServer and a custon HTTPRequestHandler."""
        Thread.__init__(self, daemon=daemon)
        self.refresh_token = None
        handler = WebRequestHandler(self)
        # not actually binding on port 0, this will ask the kernel to bind to an unused port
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.server_port = self.server.server_port

    def run(self) -> None:
        """Run the server, but only until the refresh token is written to."""
        while self.refresh_token is None:
            self.server.handle_request()


class WebRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, thread: ServerThread):
        """Hold the thread itself in the handler, so the handler can set the refresh token."""
        self.thread = thread

    def __call__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Instead of letting the server construct the handler, just make the handler callable."""
        super().__init__(*args, **kwargs)

    def end_headers(self) -> None:
        """The headers you needs for a CORS check."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header(
            "Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept"
        )
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        return super(WebRequestHandler, self).end_headers()

    def do_OPTIONS(self) -> None:
        """OPTIONS is needed for a preflight check, apparently."""
        self.send_response(200)
        self.end_headers()

    def do_GET(self) -> None:
        """This should never come up, but don't serve files or anything regardless."""
        self.send_response(200)
        self.end_headers()

    def do_POST(self) -> None:
        """Receive the refresh token from the client webpage, which will shut off the server and the thread."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        post_dict = json.loads(post_data)
        self.thread.refresh_token = post_dict["refresh_token"]
        self.send_response(200)
        self.end_headers()
