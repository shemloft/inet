import socket
import ssl
import base64
import json
import re

POP3_SERVERS = {
    'mail.ru': 'pop.mail.ru',
    'yandex.ru': 'pop.yandex.ru',
    'gmail.com': 'pop.gmail.com'
}


class SocketTools:
    CRLF = '\r\n'

    @staticmethod
    def communicate_cmd(sock, cmd):
        cmd = (cmd + SocketTools.CRLF).encode()
        # SocketTools.print_query(cmd)
        sock.sendall(cmd)
        reply = SocketTools.receive_reply(sock)
        # SocketTools.print_resp(reply)
        return reply

    @staticmethod
    def receive_reply(sock):
        reply = b''
        temp = sock.recv(1024)
        while temp:
            reply += temp
            try:
                temp = sock.recv(1024)
            except socket.timeout:
                temp = None
        return reply

    @staticmethod
    def print_query(q):
        print(f'C: {q.decode().strip(SocketTools.CRLF)}')

    @staticmethod
    def print_resp(r):
        print(f'S: {r.decode().strip(SocketTools.CRLF)}')


class UserCommunicator:
    def __init__(self):
        self.exit = False
        self.commands = ['TOP', 'HEADERS', 'DOWNLOAD', 'T', 'H', 'D']

    def get_number(self, message):
        print(message)
        cmd = input()
        if self.is_exit(cmd):
            return None
        try:
            number = int(cmd)
            return number
        except ValueError:
            print('Number should be int')
            return None

    def is_exit(self, cmd):
        if cmd.lower() == 'exit':
            self.exit = True
        return self.exit

    def get_command(self):
        print(f'Enter command. Possible commands: {", ".join(self.commands)}')
        cmd = input()
        if self.is_exit(cmd):
            return None
        if cmd.upper() not in self.commands:
            print(f'Unknown command: {cmd}')
            return None
        return cmd.upper()

    def send_message(self, message):
        print(message)


class MessageHandler:
    def __init__(self, directory):
        self.directory = directory
        self.header_re = re.compile(r'[^=](From|To|Subject|Content-Type|Date): (.+)')
        self.boundary_re = re.compile(r'Content-Type: multipart/mixed;\s+boundary=\"(.+?)\"')
        self.content_type_re = re.compile(r'Content-Type: ([\w/]+)')
        self.name_re = re.compile(r'\sname="(.+)"')
        self.after_empty_line_re = re.compile(r'(\n\n|\r\n\r\n)(.+)', re.DOTALL)

    def get_headers_from_str(self, message):
        headers = self.header_re.findall(message)
        return '\n'.join([f'{name}: {content}' for name, content in headers])

    def get_headers_and_top(self, message):
        index = message.find('\r\n\r\n')
        headers, text = message[:index], message[index:]

        headers_and_top = 'Headers:\n'
        headers_and_top += self.get_headers_from_str(headers)
        headers_and_top += '\n\nTop lines:\n'
        headers_and_top += text.strip('\n\r.')

        return headers_and_top

    def download(self, message):
        boundary_match = self.boundary_re.search(message)

        if boundary_match:
            boundary = boundary_match.group(1)
            self.process_mixed_message(boundary, message)
        else:
            self.process_text(message)

    def process_mixed_message(self, boundary, message):
        end_index_match = re.search(f'--{boundary}--', message)
        message = message[:end_index_match.start()] if end_index_match else message
        parts = re.split(f'--{boundary}', message)

        text = parts[1].strip('\n\r')
        self.process_text(text)

        attachments = parts[2:]
        for attachment in attachments:
            self.process_attachment(attachment.strip('\n\r'))

    def process_text(self, text):
        content_type_match = self.content_type_re.search(text)
        content_type = content_type_match.group(1) if content_type_match else None
        # print(content_type)

        content = self.after_empty_line_re.search(text).group(2)

        if content_type == 'text/html':
            with open(f'{self.directory}/message_text.html', 'wt') as f:
                f.write(content)
        else:
            content = self.delete_dots(content)
            with open(f'{self.directory}/message_text.txt', 'wt') as f:
                f.write(content)

    def delete_dots(self, text):
        new_text = []
        for line in text.split('\n'):
            new_text.append(line[1:] if line and line[0] == '.' else line)
        return '\n'.join(new_text)

    def process_attachment(self, attachment):
        name = self.name_re.search(attachment).group(1)
        content = self.after_empty_line_re.search(attachment).group(2)
        with open(f'{self.directory}/{name}', 'wb') as f:
            f.write(base64.b64decode(content))


class POP3Client:
    def __init__(self, login, password, directory):
        service = re.match(r'.+@(.+)', login).group(1)
        self.server_address = POP3_SERVERS[service], 995
        self.login = login
        self.password = password
        self.communicator = UserCommunicator()
        self.message_handler = MessageHandler(directory)
        self.commands = {
            'TOP': self.get_top,
            'T': self.get_top,
            'HEADERS': self.get_headers,
            'H': self.get_headers,
            'DOWNLOAD': self.download,
            'D': self.download
        }

    def authorise(self, sock):
        SocketTools.communicate_cmd(sock, f'USER {self.login}')
        SocketTools.communicate_cmd(sock, f'PASS {self.password}')

    def execute(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client = ssl.wrap_socket(client)
            client.connect(self.server_address)
            client.settimeout(1)
            SocketTools.print_resp(SocketTools.receive_reply(client))
            self.communicator.send_message('Authorising...')
            self.authorise(client)
            self.communicator.send_message('Authorised')
            while True:
                is_exit = self.communicate(client)
                if is_exit:
                    break

    def communicate(self, sock):
        number = None
        while number is None:
            number = self.communicator.get_number('Enter message number')
            if self.communicator.exit:
                return True

        if self.no_number(sock, number):
            print('No such letter')
            return

        cmd = self.communicator.get_command()
        if self.communicator.exit:
            return True
        if not cmd:
            return

        return self.commands[cmd](sock, number)

    def get_headers(self, sock, number):
        reply = SocketTools.communicate_cmd(sock, f'TOP {number} 0').decode()
        print(self.message_handler.get_headers_from_str(reply))

    def get_top(self, sock, number):
        count = self.communicator.get_number('Enter lines count')
        if self.communicator.exit:
            return True
        reply = SocketTools.communicate_cmd(sock, f'TOP {number} {count}').decode()
        print(self.message_handler.get_headers_and_top(reply))

    def download(self, sock, number):
        reply = SocketTools.communicate_cmd(sock, f'RETR {number}').decode()
        self.message_handler.download(reply)
        self.communicator.send_message('Downloaded')

    def no_number(self, sock, number):
        reply = SocketTools.communicate_cmd(sock, f'LIST {number}')
        if reply[0] != 43:
            return True


def main():
    auth_file = 'auth.json'
    directory = 'download'

    with open(auth_file, 'rt') as f:
        auth = json.load(f)

    client = POP3Client(auth['login'], auth['password'], directory)
    client.execute()


if __name__ == '__main__':
    main()
