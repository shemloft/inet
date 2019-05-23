import re
import socket
import struct

from concurrent.futures import ProcessPoolExecutor

from tools import split_range


class TCPScanner:
    def __init__(self, host, start, end):
        self.start = start
        self.end = end
        self.host = host
        self.http_re = re.compile('400 Bad Request')
        self.smtp_re = re.compile('220')
        self.pop_re = re.compile(r'\+OK')
        self.dns_packet = b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04test\x00\x00\x01\x00\x01'

    def check_ports(self):
        self._check_ports_pool(50)

    def _check_ports_pool(self, count):
        ranges = split_range(self.start, self.end, count)
        pool = ProcessPoolExecutor(count)
        
        futures = []
        for r in ranges:
            future = pool.submit(self._check_ports_tcp, *r)
            futures.append(future)
        
        result = []
        while futures:
            for f in futures:
                if f.done():
                    result.extend(f.result())
                    futures.remove(f)
        
        for port in result:
            protocol = self.check_protocol(port)
            print(f'{port} is open, protocol: {protocol}')

    def _check_ports_tcp(self, start, end):
        open_ports = []
        for port in range(start, end):
            addr = self.host, port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setblocking(False)
                s.settimeout(0.5)
                err = s.connect_ex(addr)
                if err == 0:
                    open_ports.append(port)
        return open_ports

    def check_protocol(self, port):
        mes = b'test'
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setblocking(False)
            s.settimeout(1)
            s.connect((self.host, port))
            try:
                resp = self.try_with_timeout(s.recv, 1024)
                if not resp:

                    s.sendall(struct.pack('!H', len(self.dns_packet)))
                    resp = self.try_with_timeout(s.recv, 1024)
                    if resp:
                        return self.check_data(resp)

                    s.sendall(self.dns_packet)
                    resp = self.try_with_timeout(s.recv, 2)

                    if resp:
                        return 'dns'

                return self.check_data(resp)

            except ConnectionResetError:
                return 'unknown'

    def try_with_timeout(self, func, *args):
        try:
            return func(*args)
        except socket.timeout:
            return None

    def check_data(self, data):
        if not data:
            return 'unknown'
        data = data.decode()
        if self.http_re.search(data):
            return 'http'
        if self.smtp_re.search(data):
            return 'smtp'
        if self.pop_re.search(data):
            return 'pop3'
        return 'unknown'
