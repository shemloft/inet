import json, socket
from modules import query, response, data_structures, cashing, tools

ADDRESS = ("127.0.0.1", 53)
CASH_FILE = "cash.json"
ROOT_SERVERS = (('199.9.14.201', 53),
                ('198.41.0.4', 53),
                ('199.7.91.13', 53))
Q_TYPES = [1, 2]


class DNSServer:
    def __init__(self, forwarder_addr, cash=None, iterative=True):
        self.forwarder = forwarder_addr
        self.id = 1 # последовательное упрощает атаку отравления кэша
        self.cash = cash if cash else cashing.Cash()
        self.iterative = iterative

    def execute(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(ADDRESS)
            server.settimeout(2)
            while True:
                try:
                    data, addr = server.recvfrom(1024)
                except socket.timeout:
                    continue
                resp = self.process_query(data)
                if not resp:
                    continue
                resp_b = response.ResponseHandler.make_response(resp)
                server.sendto(resp_b, addr)

    def process_query(self, data):
        q_in = query.QueryHandler.parse_query(data)
        q_in_id = q_in.header.id
        url = q_in.question.url
        q_type = q_in.question.q_type
        if q_type not in Q_TYPES:
            return None

        cash_value = self.cash.get_answer(url, q_type)
        print(cash_value)
        if cash_value:
            return self.construct_response(url, q_type, q_in_id, cash_value)
        if self.iterative:
            return self.get_response_iterative(url, q_type, q_in_id)
        else:
            return self.get_response_recurs(url, q_type, q_in_id)

    def get_response_iterative(self, url, q_type, q_in_id):
        labels = tools.Tools.get_label_list(url)
        current_ns_servers = ROOT_SERVERS
        for i in range(len(labels) - 1, -2, -1):
            current_url = '.'.join(labels[i:]) if i != -1 else url
            q_out = self.construct_query(current_url, 2 if i != -1 else q_type)
            q_out_b = query.QueryHandler.make_query(q_out)
            for server in current_ns_servers:
                data = self.send_query_get_response(q_out_b, server)
                if data:
                    break
            server_resp = response.ResponseHandler.parse_response(data)
            if server_resp.header.flags.rcode != 0:
                return self.construct_response_with_error(q_in_id, server_resp.header.flags.rcode)
            self.cash_response(server_resp)
            if i != -1:
                answer = self.cash.get_answer(current_url, 2)
                print(answer)
                if answer:
                    current_ns_servers = [(ns, 53) for ns in self.cash.get_answer(current_url, 2)][:3]
            else:
                print(current_url, q_type)
                answer = self.cash.get_answer(current_url, q_type)
                return self.construct_response(url, q_type, q_in_id, answer)

    def get_response_recurs(self, url, q_type, q_in_id):
        q_out = self.construct_query(url, q_type)
        q_out_b = query.QueryHandler.make_query(q_out)
        data = self.send_query_get_response(q_out_b, self.forwarder)
        if not data:
            return None
        forwarder_resp = response.ResponseHandler.parse_response(data)
        if forwarder_resp.header.flags.rcode != 0:
            return self.construct_response_with_error(q_in_id, forwarder_resp.header.flags.rcode)
        self.cash_response(forwarder_resp)
        cash_value = self.cash.get_answer(url, q_type)
        if not cash_value:
            cash_value = []
        return self.construct_response(url, q_type, q_in_id, cash_value)

    def send_query_get_response(self, query_b, address):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(query_b, address)
            return client.recvfrom(1024)[0]

    def cash_response(self, resp):
        for rr in resp.answers_rrs + resp.authority_rrs + resp.additional_rrs:
            self.cash.add_record(rr)
        with open(CASH_FILE, 'wt') as f:
            json.dump(self.cash.make_serializable(), f)

    def construct_response(self, url, q_type, q_id, answers_list):
        flags = data_structures.Flags(1, 0, 1, 0, 0)
        header = data_structures.Header(q_id, flags, 1, len(answers_list), 0, 0)
        question = data_structures.Question(url, q_type)
        answers = []
        for answer in answers_list:
            answers.append(data_structures.ResourceRecord(url, q_type, 60, answer))
        return response.Response(header, question, answers, [], [])

    def construct_response_with_error(self, q_id, error):
        flags = data_structures.Flags(1, 0, 1, 0, error)
        header = data_structures.Header(q_id, flags, 0, 0, 0, 0)
        return response.Response(header, None, [], [], [])

    def construct_query(self, url, q_type):
        flags = data_structures.Flags(0, 0, 1, 0, 0)
        header = data_structures.Header(self.id, flags, 1, 0, 0, 0)
        question = data_structures.Question(url, q_type)
        return query.Query(header, question)


def main():
    with open('config.txt', 'rt') as g:
        lines = g.readlines()
        addr = lines[0]
    forwarder = (addr, 53)
    with open(CASH_FILE, 'rt') as f:
        cash_j = json.load(f)
    cash = cashing.Cash.get_cash_from_json(cash_j)
    server = DNSServer(forwarder, cash, iterative=True)
    server.execute()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
