import datetime
import socket
from message import Message, convert_time, TIME1900


def parse_time(sec, msc):
    seconds = float(str(sec) + '.' + str(msc))
    t = datetime.timedelta(seconds=seconds)
    return TIME1900 + t


def get_time(data):
    resp = Message.parse_data(data)
    t1 = parse_time(resp.origin_sec, resp.origin_msc)  # отправка клиентом
    t2 = parse_time(resp.receive_sec, resp.receive_msc)  # получение сервером
    t3 = parse_time(resp.transmit_sec, resp.transmit_msc)  # отправка сервером
    t4 = parse_time(*convert_time(datetime.datetime.utcnow()))  # получение клиентом

    delay = (t4 - t3) + (t2 - t1)
    offset = ((t2 - t1) + (t3 - t4)) / 2

    UTC5 = datetime.timezone(datetime.timedelta(hours=5))
    print("delay:", delay)
    print("time from server:", datetime.datetime.utcnow() + offset + datetime.timedelta(hours=5))
    print("my time:", datetime.datetime.utcnow() + datetime.timedelta(hours=5))


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(('127.0.0.1', 123))
        print("Press ENTER to get time")
        while True:
            i = input()
            time = datetime.datetime.utcnow()
            query = Message.make_query(*convert_time(time))
            client.send(query)
            data = client.recv(1024)
            get_time(data)


if __name__ == '__main__':
    main()
