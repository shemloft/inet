import socket
import select
from threading import Thread

from .connection import Connection


class ProxyServer:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('127.0.0.1', 8080))
        self.server.listen(10)
        self.server.setblocking(0)
        self.input_list = [self.server]

    def execute(self):
        while True:
            readable, _, _ = select.select(self.input_list, [], [])
            for s in readable:
                if s is self.server:
                    self.accept()

    def accept(self):
        browser, address = self.server.accept()
        conn = Connection(browser)
        thread = Thread(target=conn.execute)
        thread.start()
