import struct
from datetime import timedelta, datetime

TIME1900 = datetime(1900, 1, 1)


def convert_time(t, delta=None):
    td = t - TIME1900
    if delta:
        td += timedelta(seconds=delta)
    seconds = td.total_seconds()
    split_num = str(seconds).split('.')
    return int(split_num[0]), int(split_num[1])


class Message:
    MESSAGE_FORMAT = "!BBBbiIIIIIIIIII"

    def __init__(self, fields=None):
        if fields:
            self.set_fields(fields)
        else:
            self.li = 0
            self.vn = 0
            self.mode = 0
            self.stratum = 0
            self.poll = 0
            self.precision = 0
            self.root_delay = 0
            self.root_dispersion = 0
            self.ref_id = 0
            self.reference_sec, self.reference_msc = 0, 0
            self.origin_sec, self.origin_msc = 0, 0
            self.receive_sec, self.receive_msc = 0, 0
            self.transmit_sec, self.transmit_msc = 0, 0

    def set_fields(self, fields):
        self.li, self.vn, self.mode = Message.unpack_flags(fields[0])
        (self.stratum, self.poll, self.precision,
         self.root_delay, self.root_dispersion, self.ref_id) = fields[1:7]
        self.reference_sec, self.reference_msc = fields[7:9]
        self.origin_sec, self.origin_msc = fields[9:11]
        self.receive_sec, self.receive_msc = fields[11:13]
        self.transmit_sec, self.transmit_msc = fields[13:15]

    def get_bytes(self):
        flags_bit = f"{self.li:02b}{self.vn:03b}{self.mode:03b}"
        flags = int(flags_bit, 2)
        return struct.pack(
            self.MESSAGE_FORMAT, flags, self.stratum, self.poll, self.precision,
            self.root_delay, self.root_dispersion, self.ref_id, self.reference_sec, self.reference_msc,
            self.origin_sec, self.origin_msc,
            self.receive_sec, self.receive_msc,
            self.transmit_sec, self.transmit_msc)

    @staticmethod
    def parse_data(data):
        fields = struct.unpack(Message.MESSAGE_FORMAT, data)
        return Message(fields)

    @staticmethod
    def make_query(time_sec, time_msc):
        message = Message()
        message.vn = 4
        message.mode = 3
        message.transmit_sec = time_sec
        message.transmit_msc = time_msc
        return message.get_bytes()


    @staticmethod
    def unpack_flags(flags):
        flags_bit = f"{flags:08b}"
        return int(flags_bit[0:2], 2), int(flags_bit[2:5], 2), int(flags_bit[5:], 2)