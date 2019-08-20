from . import tools, data_structures


class Query:
    def __init__(self, header, question):
        self.header = header
        self.question = question

    def __str__(self):
        return f'url: {self.question.url}, type: {self.question.q_type}'


class QueryHandler:

    @staticmethod
    def make_query(query):
        return query.header.get_header_bytes() + query.question.get_question_bytes()

    @staticmethod
    def parse_query(data):
        header = data_structures.Header.get_header_from_data(data[0:12])
        question, _ = data_structures.Question.get_question_from_data(data[12:])
        return Query(header, question)

