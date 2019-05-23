import socket
import ssl

from .tools import SocketTools, OK_REPLY
from .http_parser import HTTPRequest, HTTPResponse


class Connection:
    def __init__(self, browser):
        self.browser = browser

    def execute(self):
        query = SocketTools.receive(self.browser)
        if not query:
            return
        req = HTTPRequest(query)
        if req.method == b'CONNECT':
            forwarder_conn = self.make_a_connection(req)
            self.process_dialog(forwarder_conn)
        else:
            self.send_message(req)

    def make_a_connection(self, req):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((req.host, 443))
        self.browser.sendall(OK_REPLY.encode())
        self.browser = ssl.wrap_socket(
            self.browser, keyfile='server.key', certfile='server.crt',
            server_side=True, do_handshake_on_connect=False)
        try:
            self.browser.do_handshake()
        except Exception:
            pass

        self.browser.setblocking(0)
        client.setblocking(0)
        self.browser.settimeout(3)
        client.settimeout(3)

        context = ssl._create_default_https_context()
        client = context.wrap_socket(client, server_hostname=req.host)

        return client

    def process_dialog(self, forwarder):
        while True:
            req = SocketTools.receive(self.browser)
            if req:
                forwarder.sendall(req)
            reply = SocketTools.receive(forwarder)
            if reply:
                response = HTTPResponse(reply).get_response()
                self.browser.sendall(response)

    def send_message(self, req):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((req.host, int(req.host_port) if req.host_port else 80))
            client.sendall(req.request)
            response = SocketTools.receive(client)
            self.browser.sendall(response)
