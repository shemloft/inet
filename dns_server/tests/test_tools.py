import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir, 'modules'))
from modules import tools


class ToolsTests(unittest.TestCase):
    def test_correct_parse(self):
        url = 'www.first.second.com'
        expected_list = ['first', 'second', 'com']
        self.assertEqual(expected_list, tools.Tools.get_label_list(url))

    def test_correct_string(self):
        label_list = ['first', 'second', 'com']
        expected_result = b'\x05first\x06second\x03com\x00'
        self.assertEqual(expected_result, tools.Tools.get_labels_string(label_list))

    def test_correct_labels_from_string(self):
        b_labels = b'\x05first\x06second\x03com\x00'
        expected_list = ['first', 'second', 'com']
        self.assertEqual((expected_list, b''), tools.Tools.parse_binary_labels(b_labels))


if __name__ == '__main__':
    unittest.main()
