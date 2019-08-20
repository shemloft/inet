import unittest
import sys
import os
import struct
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir, 'modules'))
from modules import query, data_structures, response


# class QueryTests(unittest.TestCase):
#
#     def test_full_query(self):
#         q = query.Query(data_structures.Header(17, data_structures.Flags(0, 0, 1, 0, 0), 1, 0, 0, 0),
#                         data_structures.Question('example.com', 1))
#         q_res = query.QueryParser.make_query(q)
#         q_exp = b'\x00\x11\x01\x00\x00\x01\x00\x00\x00\x00' \
#                 b'\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'
#         self.assertEqual(q_res, q_exp)
#
#     def test_not_ascii_query(self):
#         q = query.Query(data_structures.Header(17, data_structures.Flags(0, 0, 1, 0, 0), 1, 0, 0, 0),
#                         data_structures.Question('екатеринбург.рф', 1))
#         q_res = query.QueryParser.make_query(q)
#         q_exp = b'\x00\x11\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00' \
#                 b'\x13xn--80acgfbsl1azdqr\x08xn--p1ai\x00\x00\x01\x00\x01'
#         self.assertEqual(q_res, q_exp)
#
#     def test_query_parse(self):
#         # q = query.Query(data_structures.Header(17, data_structures.Flags(0, 0, 1, 0, 0), 1, 0, 0, 0),
#         #                 data_structures.Question('example.com', 1))
#         # q_res = query.QueryParser.make_query(q)
#         data = b'\x00\x11\x01\x00\x00\x01\x00\x00\x00\x00' \
#                 b'\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'
#         q = query.QueryParser.parse_query(data)
#         q_exp = query.Query(data_structures.Header(17, data_structures.Flags(0, 0, 1, 0, 0), 1, 0, 0, 0),
#                             data_structures.Question('example.com', 1))
#         self.assertEqual(q.header.id, 17)
#         self.assertEqual(q.question.url, 'example.com')
#         self.assertEqual(q.question.q_type, 1)


class ResponseTest(unittest.TestCase):
    def test_response(self):
        data = b'\xaa\xaa\x85\x00\x00\x01\x00\x02\x00\x04\x00\x02\x02e1\x02ru' \
               b'\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x01,\x00'\
               b'\x04\xd4\xc1\xa3\x07\xc0\x0c\x00\x01\x00\x01\x00\x00\x01,\x00' \
               b'\x04\xd4\xc1\xa3\x06\xc0\x0c\x00\x02\x00\x01\x00\x00\x01,\x00' \
               b'\t\x02ns\x03ngs\xc0\x0f\xc0\x0c\x00\x02\x00\x01\x00\x00\x01,' \
               b'\x00\x06\x03ns2\xc0F\xc0\x0c\x00\x02\x00\x01\x00\x00\x01,\x00' \
               b'\x06\x03ns1\xc0\x0c\xc0\x0c\x00\x02\x00\x01\x00\x00\x01,\x00\x06' \
               b'\x03ns2\xc0\x0c\xc0j\x00\x01\x00\x01\x00\x00\x01,\x00\x04\xd4\xc1' \
               b'\xa3\x06\xc0|\x00\x01\x00\x01\x00\x00\x01,\x00\x04\xd4\xc1\xa3\x07'
        resp = response.ResponseHandler.parse_response(data)
        print(resp)



if __name__ == '__main__':
    unittest.main()