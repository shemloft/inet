import struct
from . import tools


class Flags:
    def __init__(self, qr, aa, rd, ra, rcode):
        self.qr = qr  # 0 -- query, 1 -- response
        self.aa = aa  # 0 -- authoritive
        self.rd = rd  # recursion desired
        self.ra = ra  # recursion available
        self.rcode = rcode  # result code

    def get_bit_str(self):
        return f"{self.qr}0000{self.aa}0{self.rd}{self.ra}000{self.rcode:04b}"

    @staticmethod
    def get_flags_from_data(data):
        bit_string = '{:08b}{:08b}'.format(data[0], data[1])
        qr = bit_string[0]
        aa = bit_string[5]
        rd = bit_string[7]
        ra = bit_string[8]
        rcode = int(bit_string[12:], 2)
        return Flags(qr, aa, rd, ra, rcode)


class Header:
    def __init__(self, id, flags,
                 question_count, answer_count,
                 authority_count, additional_count):
        self.id = id
        self.flags = flags
        self.question_count = question_count
        self.answer_count = answer_count
        self.authority_count = authority_count
        self.additional_count = additional_count

    def get_header_string(self):
        return f'{self.id:016b}{self.flags.get_bit_str()}{self.question_count:016b}' \
               f'{self.answer_count:016b}{self.authority_count:016b}{self.additional_count:016b}'

    def get_header_bytes(self):
        string = self.get_header_string()
        return int(string, 2).to_bytes((len(string) + 7) // 8, 'big')

    @staticmethod
    def get_header_from_data(data):
        data_id = struct.unpack('!H', data[0:2])[0]
        flags = Flags.get_flags_from_data(data[2:4])
        (question_count,
         answer_count,
         authority_count,
         additional_count) = struct.unpack('!HHHH', data[4:])

        return Header(data_id, flags,
                      question_count,
                      answer_count,
                      authority_count,
                      additional_count)


class Question:
    def __init__(self, url, q_type, q_class=1):
        self.url = url
        self.q_type = q_type
        self.q_class = q_class

    def get_question_bytes(self):
        q_name = tools.Tools.get_labels_string(tools.Tools.get_label_list(self.url))
        q_type = self.q_type.to_bytes(2, 'big')
        q_class = self.q_class.to_bytes(2, 'big')
        return q_name + q_type + q_class

    @staticmethod
    def get_question_from_data(data):
        labels, data = tools.Tools.parse_binary_labels(data)
        q_type = int.from_bytes(data[0:2], 'big')
        q_class = int.from_bytes(data[2:4], 'big')
        url = tools.Tools.get_url(labels)
        return Question(url, q_type, q_class), data[4:]


class ResourceRecord:
    def __init__(self, url, r_type, ttl, data):
        self.url = url
        self.r_type = r_type
        self.r_class = 1
        self.ttl = ttl
        self.data = data

    def __str__(self):
        return f'{self.url}, {self.r_type}, {self.data}'

    def get_record_bytes(self):
        name = tools.Tools.get_labels_string(tools.Tools.get_label_list(self.url))
        r_type = self.r_type.to_bytes(2, 'big')
        r_class = self.r_class.to_bytes(2, 'big')
        ttl = self.ttl.to_bytes(4, 'big')
        data_b = None
        if self.r_type == 1:
            data_b = struct.pack('!4B', *([int(i) for i in self.data.split('.')]))
        elif self.r_type == 2:
            data_b = tools.Tools.get_labels_string(tools.Tools.get_label_list(self.data))
        else:
            return
        data_len = len(data_b).to_bytes(2, 'big')
        return name + r_type + r_class + ttl + data_len + data_b


    @staticmethod
    def get_rr_from_data(data, total_data):
        # if bin(data[0])[2:4]=='11':
        labels, data = tools.Tools.parse_name(data, total_data)
        url = tools.Tools.get_url(labels)
        r_type = int.from_bytes(data[0:2], 'big')
        r_class = int.from_bytes(data[2:4], 'big')
        ttl_in_sec = struct.unpack('!L', data[4:8])[0]
        data_length = struct.unpack('!H', data[8:10])[0]
        r_data_b = data[10:10 + data_length]
        r_data = ResourceRecord.get_r_data(r_data_b, r_type, total_data)
        # print("r_data:", r_data)
        if not r_data:
            return None, data[10+data_length:]
        return ResourceRecord(url, r_type, ttl_in_sec, r_data), data[10+data_length:]

    @staticmethod
    def get_r_data(data, r_type, total_data):
        if r_type == 1:
            ipv4 = struct.unpack('!4B', data)
            return '.'.join(map(str, ipv4))
        elif r_type == 2:
            domain_name_labels, _ = tools.Tools.parse_name(data, total_data)
            return '.'.join(domain_name_labels)
        return


