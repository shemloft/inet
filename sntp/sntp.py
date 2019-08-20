import socket
from datetime import datetime, timezone, timedelta
from message import Message, convert_time
# http://www.faqs.org/rfcs/rfc1361.html

ADDRESS = ('127.0.0.1', 123)


class SNTPServer:
    def __init__(self, shift_in_sec):
        self.shift_in_sec = shift_in_sec

    def execute_udp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(ADDRESS)
            while True:
                server.settimeout(2)
                try:
                    data, addr = server.recvfrom(1024)
                    receive_time = datetime.utcnow()
                except socket.timeout:
                    continue
                if not data:
                    continue
                response = self.get_response(data, receive_time)
                server.sendto(response, addr)

    def execute_tcp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(ADDRESS)
            server.listen(1)
            conn, addr = server.accept()
            while True:
                server.settimeout(2)
                try:
                    data = conn.recv(1024)
                    receive_time = datetime.utcnow()
                except socket.timeout:
                    continue
                if not data:
                    continue
                response = self.get_response(data, receive_time)
                conn.send(response)

    def get_response(self, query, receive_time):
        query_message = Message.parse_data(query)
        response_message = self.get_response_message(query_message, receive_time)
        return response_message.get_bytes()

    def get_response_message(self, query_message, receive_time):
        resp = query_message
        resp.li = 0
        resp.mode = 4
        resp.stratum = 1
        resp.precision = 0
        resp.root_delay = 0
        resp.root_dispersion = 0
        resp.ref_id = int.from_bytes(b'OS', 'big')
        resp.reference_sec, resp.reference_msc = 0, 0
        resp.origin_sec, resp.origin_msc = query_message.transmit_sec, query_message.transmit_msc
        resp.receive_sec, resp.receive_msc = convert_time(receive_time, self.shift_in_sec)
        resp.transmit_sec, resp.transmit_msc = convert_time(datetime.utcnow(), self.shift_in_sec)
        return resp


def main():
    with open("config.txt", 'rt') as f:
        shift_in_sec = int(f.readlines()[0])
        print(shift_in_sec)
    server = SNTPServer(shift_in_sec)
    server.execute_tcp()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
