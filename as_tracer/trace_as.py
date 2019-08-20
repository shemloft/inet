import argparse
import subprocess
import re
import urllib.request
import json

TRACERT_ERROR = "Problems with finding route to "
PARSING_ERROR = "Route wasn't found to "
NETWORK_INFO_REQUEST = "https://stat.ripe.net/data/network-info/data.json?resource="
WHOIS_REQUEST = "https://stat.ripe.net/data/whois/data.json?resource="
AS_OVERVIEW_REQUEST = "https://stat.ripe.net/data/as-overview/data.json?resource="

GRAY_IPS = ((bytes((10, 0, 0, 0)), bytes((255, 0, 0, 0))),
           (bytes((172, 16, 0, 0)), bytes((255, 240, 0, 0))),
           (bytes((192, 168, 0, 0)), bytes((255, 255, 0, 0))))


class Route:
    def __init__(self, name, ip):
        self.route = []
        self.target_name = name
        self.target_ip = ip

    def add_node(self, node):
        self.route.append(node)


class Node:
    def __init__(self, ip):
        self.ip = ip
        self.gray = self._check_if_ip_is_gray()
        self.AS = None
        self.country = None
        self.holder = None

    def _check_if_ip_is_gray(self):
        ip_byte_list = [int(b) for b in self.ip.split('.')]
        ip_bytes = bytes(ip_byte_list)
        for net, mask in GRAY_IPS:
            ip_with_mask = []
            for i, byte in enumerate(mask):
                ip_with_mask.append(byte & ip_bytes[i])
            if bytes(ip_with_mask) == net:
                return True
        return False

    def get_api_info(self):
        if self.gray:
            return
        with urllib.request.urlopen(
                "https://stat.ripe.net/data/rir/data.json?resource={}&lod=2".format(self.ip)) as f:
            result = f.read().decode('utf-8')
            self.country = json.loads(result)['data']['rirs'][0]['country']

        with urllib.request.urlopen(
                 "https://stat.ripe.net/data/prefix-overview/data.json?resource={}".format(self.ip)) as f:
            result = f.read().decode('utf-8')
            asns = json.loads(result)['data']['asns']
            if not asns:
                return
            self.AS = 'AS' + str(asns[0]['asn'])
            self.holder = asns[0]['holder']


def get_tracert_result(target):
    command = ['tracert', '-d', target]
    result = subprocess.run(command, #shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            encoding='cp866',
                            errors='ignore')
    if result.returncode:
        raise ValueError(TRACERT_ERROR + target)

    return result.stdout


def parse_tracert_result(target, tracert_result):
    print(tracert_result)
    result_lines = [line for line in tracert_result.split('\n') if line != '']
    ip_re_str = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    ip_re = re.compile(ip_re_str)
    match = ip_re.search(result_lines[0])
    if not match:
        raise ValueError(PARSING_ERROR + target)

    name = None if ip_re.search(target) else target
    ip = match.group(1)
    route = Route(name, ip)
    router_entry_re = re.compile(r'\s*(\d+)\s+(\d+\s+ms\s+|\*\s+){3}' + r'({})?'.format(ip_re_str))

    # first_router_entry = find_first_router_entry(router_entry_re, result_lines)

    # if not first_router_entry:
    #     raise ValueError(PARSING_ERROR + target)

    for i in range(2, len(result_lines)):
        line = result_lines[i]
        match = router_entry_re.match(line)
        if not match:
            continue
        count = int(match.group(1))
        last_time = match.group(2).strip()
        if last_time == '*':
            continue
        ip = match.group(3)
        node = Node(ip)
        route.add_node(node)

    return route


def find_first_router_entry(router_entry_re, result_lines):
    for i, line in enumerate(result_lines):
        if router_entry_re.match(line):
            return i
    return None

def print_route(route):
    column_max = []
    attributes = ('ip', 'AS', 'country', 'holder')
    names = ('№', 'IP', 'AS', 'Страна', 'Провайдер')
    column_max.append(max(len(names[0]),len(str(len(route.route)))))
    for i, a in enumerate(attributes):
        data_lengths = [len(data) for data in [getattr(n, a) for n in route.route] if data]
        column_max.append(
            max(len(names[i+1]),
                max(data_lengths if data_lengths else [0])))
    format_str = ''
    for c_max in column_max:
        format_str += '{' + ':>{}'.format(c_max) + '}    '
    print(format_str.format(*names))
    for i, r in enumerate(route.route):
        print(format_str.format(i + 1, r.ip,
                                r.AS if r.AS else '',
                                r.country if r.country else '',
                                r.holder if r.holder else ''))


def get_parser():
    parser = argparse.ArgumentParser(description='DNS client')
    parser.add_argument('target', help='ip address or domain name')
    return parser.parse_args()


def main():
    args = get_parser()
    target = args.target

    tracert_result = get_tracert_result(target)

    route = parse_tracert_result(target, tracert_result)

    for node in route.route:
        node.get_api_info()

    print_route(route)


if __name__ == '__main__':
    main()