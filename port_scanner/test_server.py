import socket
import argparse


def get_parser():
    parser = argparse.ArgumentParser(description='Start udp server on port')
    parser.add_argument('port', type=int, help='host to check')
    return parser.parse_args()


def main():
    args = get_parser()
    ADDRESS = '127.0.0.1', args.port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(ADDRESS)
        server.settimeout(2)
        while True:
            try:
                data, addr = server.recvfrom(1024)
                print(addr)
            except socket.timeout:
                continue


if __name__ == '__main__':
    main()