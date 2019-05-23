import sys

from modules.proxy_server import ProxyServer


def main():
    proxy = ProxyServer()
    try:
        proxy.execute()
    except KeyboardInterrupt:
        print('shutdown')
        sys.exit(1)


if __name__ == '__main__':
    main()
