import ssl
import socket
import json
import base64
from mimetypes import guess_type


def encode_iterable(iterable):
    new_iterable = []
    for i in iterable:
        if isinstance(i, str):
            new_iterable.append(i.encode())
        else:
            new_iterable.append(i)
    return new_iterable


class Attachment:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.mime = guess_type(self.name)[0]
        with open(path, 'rb') as f:
            self.content = f.read()


class SocketTools:
    CRLF = '\r\n'

    @staticmethod
    def communicate_cmd(sock, cmd, *, b64=False, bytes=False):
        if not bytes:
            c1 = base64.b64encode(cmd.encode()) + SocketTools.CRLF.encode()
            c2 = (cmd + SocketTools.CRLF).encode()
            cmd = base64.b64encode(cmd.encode()) + SocketTools.CRLF.encode() \
                if b64 else (cmd + SocketTools.CRLF).encode()
        SocketTools.print_query(cmd)
        sock.sendall(cmd)
        reply = sock.recv(1024)
        SocketTools.print_resp(reply)

    @staticmethod
    def print_query(q):
        print(f'C: {q.decode().strip(SocketTools.CRLF)}')

    @staticmethod
    def print_resp(r):
        print(f'S: {r.decode().strip(SocketTools.CRLF)}')


class Message:
    def __init__(self, text_lines, mail_from, mail_to, subject, attachments):
        self.boundary = 'LeBoundare2007'
        self.text_lines = text_lines
        self.mail_from = mail_from
        self.mail_to = mail_to
        self.subject = subject
        self.attachments = attachments

    def get_message(self):
        message = []

        message.extend(self.get_headers())
        message.extend(self.get_text())
        message.extend(self.get_attachments())

        message.append(f'--{self.boundary}--')
        message.append('.\n')

        return b'\n'.join(encode_iterable(message))

    def get_headers(self):
        return [
            'From: ' + self.mail_from,
            'To: ' + ', '.join(self.mail_to),
            'Subject: ' + self.subject,
            'MIME-Version: 1.0',
            f'Content-Type: multipart/mixed; boundary="{self.boundary}"',
            ''
        ]

    def get_text(self):
        text = [
            '--{}'.format(self.boundary),
            'Content-Transfer-Encoding: 8bit',
            'Content-Type: text/plain; charset=utf-8',
            ''
        ]
        text.extend(self.shield_dots(self.text_lines))
        return text

    def shield_dots(self, text_lines):
        return [f'.{line}' if line[0] == '.' else line for line in text_lines]

    def get_attachments(self):
        attach_list = []
        for a in self.attachments:
            current_attach = [
                '--{}'.format(self.boundary),
                f'Content-Disposition: attachment; filename="{a.name}"',
                'Content-Transfer-Encoding: base64',
                f'Content-Type: {a.mime}; name="{a.name}"',
                '',
                base64.b64encode(a.content)
            ]
            attach_list.extend(current_attach)
        return attach_list


class SMTPClient:
    SERVER_ADDRESS = 'smtp.yandex.ru', 465

    def __init__(self, auth_json, message):
        self.login = auth_json['login']
        self.password = auth_json['password']
        self.mail_address = auth_json['mail']
        self.message = message

    def authorise(self, sock):
        SocketTools.communicate_cmd(sock, 'EHLO ' + self.mail_address)
        SocketTools.communicate_cmd(sock, 'AUTH LOGIN')
        SocketTools.communicate_cmd(sock, self.login, b64=True)
        SocketTools.communicate_cmd(sock, self.password, b64=True)

    def send_mail(self, sock, to, message):
        SocketTools.communicate_cmd(sock, 'MAIL FROM:' + self.mail_address)
        for t in to:
            SocketTools.communicate_cmd(sock, 'RCPT TO:' + t)
        SocketTools.communicate_cmd(sock, 'DATA')
        SocketTools.communicate_cmd(sock, message, bytes=True)

    def execute(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client = ssl.wrap_socket(client)
            client.connect(self.SERVER_ADDRESS)
            connect_response = client.recv(1024)
            SocketTools.print_resp(connect_response)
            self.authorise(client)
            self.send_mail(client, self.message.mail_to, self.message.get_message())


def main():
    auth_file = 'auth.json'
    text_file = 'data/text.txt'
    config_file = 'data/config.json'

    with open(auth_file, 'rt') as f:
        auth = json.load(f)

    with open(text_file, 'rt') as f:
        text_lines = [line.strip('\n') for line in f.readlines()]

    with open(config_file, 'rt') as f:
        config = json.load(f)

    attachments = [Attachment(name, 'data/' + name) for name in config['attachments']]
    message = Message(text_lines, auth['mail'], config['to'], config['subject'], attachments)
    client = SMTPClient(auth, message)
    client.execute()


if __name__ == '__main__':
    main()
