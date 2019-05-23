import socket
import threading
import time
import struct

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

from tools import split_range


class PacketHandler:

    @staticmethod
    def get_ip_packet_data(ip_packet):
        length = int(f'{ip_packet[0]:08b}'[4:], 2) * 4  # длина заголовка ip пакета в 32 битных словах
        return ip_packet[length:]

    @staticmethod
    def get_icmp_type_code_inner_ip(icmp_packet):
        msg_type = icmp_packet[0]
        msg_code = icmp_packet[1]
        inner_ip = icmp_packet[8:] # 2-3 -- checksum, 4-7 -- not_used if type 3
        return msg_type, msg_code, inner_ip

    @staticmethod
    def get_src_dest_port(udp_packet):
        return struct.unpack('!HH', udp_packet[:4])


def get_port_if_closed(data):
    icmp_packet = PacketHandler.get_ip_packet_data(data)
    msg_type, msg_code, inner_ip = PacketHandler.get_icmp_type_code_inner_ip(icmp_packet)
    udp_packet = PacketHandler.get_ip_packet_data(inner_ip)
    src_port, dest_port = PacketHandler.get_src_dest_port(udp_packet)

    if (msg_type, msg_code) == (3, 3):
        return dest_port
    return None


class UDPScanner:
    def __init__(self, host, start, end):
        self.start = start
        self.end = end
        self.host = host
        self.protocol_checker = ProtocolChecker()

    def check_ports(self):
        if self.host != '127.0.0.1':
            checker = TimeoutBasedUdpScanner(self.host, self.start, self.end)
            open_ports = checker.get_open_ports()
        else:
            checker = ICMPBasedUdpScanner(self.host, self.start, self.end)
            open_ports = checker.get_open_ports()

        for port in open_ports:
            protocol = self.protocol_checker.check_protocol(self.host, port)
            print(f'{port} is open, protocol: {protocol}')


class ICMPBasedUdpScanner:
    def __init__(self, host, start, end):
        self.start = start
        self.end = end
        self.host = host
        self.closed = []
        self.stop = False

    def get_open_ports(self):
        self.check_ports_icmp(50)
        open_ports = set(range(self.start, self.end)) - set(self.closed)
        return open_ports

    def sniffing(self):
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as s:
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            s.settimeout(4)
            s.setblocking(False)
            while True:
                if self.stop:
                    break
                try:
                    data = s.recvfrom(65565)[0]
                except socket.timeout:
                    continue
                except Exception:
                    continue
                port = get_port_if_closed(data)
                if port:
                    self.closed.append(port)

    def check_ports_icmp(self, count):

        snif = threading.Thread(target=self.sniffing, args=())
        snif.start()
        time.sleep(2)
        
        pool = ThreadPoolExecutor(count)
        ranges = split_range(self.start, self.end, count)
        futures = []
        for r in ranges:
            future = pool.submit(self.send_ranges, *r)
            futures.append(future)

        while futures:
            for f in futures:
                if f.done():
                    futures.remove(f)

        self.stop = True
        snif.join()

    def send_ranges(self, start, end):  
        for port in range(start, end):
            self.send_udp(port)

    def send_udp(self, port):
        #time.sleep(1)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            try:
                sender.sendto(port.to_bytes(2, 'big'), (self.host, port))
            except Exception:
                #pass
                print('exc')
        time.sleep(0.2)


class TimeoutBasedUdpScanner:
    def __init__(self, host, start, end):
        self.start = start
        self.end = end
        self.host = host

    def get_open_ports(self):
        return self._check_ports_pool(3)

    def _check_ports_pool(self, count):
        pool = ProcessPoolExecutor(count)
        ranges = split_range(self.start, self.end, count)
        futures = []
        for r in ranges:
            future = pool.submit(self._check_ports_udp, *r)
            futures.append(future)
        result = []
        while futures:
            for f in futures:
                if f.done():
                    result.extend(f.result())
                    futures.remove(f)
        print(result)
        return result

    def _check_ports_udp(self, start, end):
        test = b'test'
        open_ports = []
        for port in range(start, end):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                addr = self.host, port
                s.settimeout(1)
                s.sendto(test, addr)
                try:
                    data = s.recv(1024)
                    print(data)
                except socket.timeout:
                    open_ports.append(port)
        return open_ports


class ProtocolChecker:
    def __init__(self):
        self.dns_packet = b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x04test\x00\x00\x01\x00\x01'

        self.sntp_packet = b'#\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
                           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\x85' \
                           b'H\xaf\x00\x04\xed\xf1'

    def check_protocol(self, host, port):
        if self._send_msg(host, port, self.dns_packet):
            return 'dns'
        if self._send_msg(host, port, self.sntp_packet):
            return 'sntp'
        return 'unknown'

    def _send_msg(self, host, port, msg):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            addr = host, port
            # print(addr)
            s.settimeout(1)
            s.sendto(msg, addr)
            try:
                data = s.recvfrom(1024)
                return True
            except socket.timeout:
                return False
