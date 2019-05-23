import socket


class SocketTools:
    @staticmethod
    def receive(sock):
        data = b""
        t = sock.timeout
        sock.settimeout(1)
        while True:
            try:
                temp = sock.recv(1024)
            except socket.timeout:
                break
            if not temp:
                break
            data += temp
        sock.settimeout(t)
        return data


class RequestHandler:
    _new_line = '\n'

    @staticmethod
    def get_request(lines):
        lines.append(RequestHandler._new_line)
        return RequestHandler._new_line.join(lines)


OK_REPLY = RequestHandler.get_request(['HTTP/1.1 200 OK'])
