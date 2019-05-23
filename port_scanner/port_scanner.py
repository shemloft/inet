import argparse

from tcp_scanner import TCPScanner
from udp_scanner import UDPScanner


def check_port(p):
    try:
        port = int(p)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{p} is an invalid port')
    if port < 0 or port > 65535:
        raise argparse.ArgumentTypeError(f'{port} is an invalid port')
    return port


def check_socket_type(socket_type):
    up_socket_type = socket_type.upper()
    if up_socket_type not in ('TCP', 'UDP'):
        raise argparse.ArgumentTypeError(
            '{} is an invalid socket type'.format(up_socket_type))
    return up_socket_type


def get_parser():
    parser = argparse.ArgumentParser(description='Port scanner')

    parser.add_argument('host', help='host to check')
    parser.add_argument('start', type=check_port, help='Start of range')
    parser.add_argument('end', type=check_port, help='End of range')

    parser.add_argument('-s', '--socket_type', type=check_socket_type,
                        default='TCP', help='socket type')

    return parser.parse_args()


def main():
    args = get_parser()
    host = args.host
    start = args.start
    end = args.end
    s = args.socket_type

    if s == 'TCP':
        s = TCPScanner(host, start, end)
        s.check_ports()
    else:
        s = UDPScanner(host, start, end)
        s.check_ports()


if __name__ == '__main__':
    main()
