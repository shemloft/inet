import struct
from . import data_structures


class Response:
    def __init__(self, header, question,
                 answers_rrs, authority_rrs, additional_rrs):
        self.header = header
        self.question = question
        self.answers_rrs = answers_rrs
        self.authority_rrs = authority_rrs
        self.additional_rrs = additional_rrs

    def __str__(self):
        return f'answers: {self.rrs_str(self.answers_rrs)}\n\r' \
               f'authority: {self.rrs_str(self.authority_rrs)}\n\r' \
               f'additional: {self.rrs_str(self.additional_rrs)}\n\r'

    def rrs_str(self, rr_list):
        return '; '.join([str(rr) for rr in rr_list])


class ResponseHandler:

    @staticmethod
    def make_response(response):
        resp_str = response.header.get_header_bytes()
        resp_str += b'' if not response.question else response.question.get_question_bytes()
        for rr in response.answers_rrs + response.authority_rrs + response.additional_rrs:
            resp_str += rr.get_record_bytes()
        return resp_str

    @staticmethod
    def parse_response(data):
        total_data = data
        header = data_structures.Header.get_header_from_data(data[0:12])
        question, data = data_structures.Question.get_question_from_data(data[12:])

        response = Response(header, question, [], [], [])

        for i in range(0, header.answer_count):
            rr, data = data_structures.ResourceRecord.get_rr_from_data(data, total_data)
            if rr:
                response.answers_rrs.append(rr)

        for i in range(0, header.authority_count):
            rr, data = data_structures.ResourceRecord.get_rr_from_data(data, total_data)
            if rr:
                response.authority_rrs.append(rr)

        for i in range(0, header.additional_count):
            rr, data = data_structures.ResourceRecord.get_rr_from_data(data, total_data)
            if rr:
                response.additional_rrs.append(rr)

        return response
