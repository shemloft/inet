import unittest
import trace_as


class TracertOutputParseTests(unittest.TestCase):

    def test_correct_output_name(self):
        output = \
'''Трассировка маршрута к yandex.ru [77.88.55.50] с максимальным числом прыжков 30:

  1     8 ms     7 ms     6 ms  217.24.185.33
  2    71 ms    17 ms     9 ms  10.10.11.93
  3    10 ms     8 ms     9 ms  217.24.176.200
  4    15 ms     7 ms     8 ms  194.85.107.57
  5    42 ms    39 ms    40 ms  77.88.55.50

Трассировка завершена.'''
        route = trace_as.parse_tracert_result('yandex.ru', output)
        self.assertEqual('yandex.ru', route.target_name)
        self.assertEqual('77.88.55.50', route.target_ip)
        self.assertEqual(
            [node.ip for node in route.route],
            ['217.24.185.33', '10.10.11.93', '217.24.176.200', '194.85.107.57', '77.88.55.50'])

    def test_correct_output_ip(self):
        output = \
'''Трассировка маршрута к 77.88.55.50 с максимальным числом прыжков 30

  1    10 ms     7 ms     8 ms  217.24.185.33
  2    21 ms     9 ms    15 ms  10.10.11.93
  3    10 ms    14 ms     8 ms  217.24.176.200
  4    10 ms     9 ms     7 ms  194.85.107.57
  5    40 ms    41 ms    40 ms  77.88.55.50

Трассировка завершена.'''
        route = trace_as.parse_tracert_result('77.88.55.50', output)
        self.assertEqual(None, route.target_name)
        self.assertEqual('77.88.55.50', route.target_ip)
        self.assertEqual(
            [node.ip for node in route.route],
            ['217.24.185.33', '10.10.11.93', '217.24.176.200', '194.85.107.57', '77.88.55.50'])

    def test_output_with_asterisk(self):
        output = \
'''Трассировка маршрута к 77.88.55.50 с максимальным числом прыжков 30

  1    10 ms     7 ms     8 ms  217.24.185.33
  2    21 ms     9 ms    15 ms  10.10.11.93
  3     *        *        *     Превышен интервал ожидания для запроса.

Трассировка завершена.'''
        route = trace_as.parse_tracert_result('77.88.55.50', output)
        self.assertEqual(None, route.target_name)
        self.assertEqual('77.88.55.50', route.target_ip)
        self.assertEqual(
            [node.ip for node in route.route],
            ['217.24.185.33', '10.10.11.93'])

    def test_incorrect_output_no_result(self):
        output = "Не удается разрешить системное имя узла vk.com."
        self.assertRaises(
            ValueError,
            trace_as.parse_tracert_result,
            'vk.com', output)

    def test_incorrect_output_result_with_problems(self):
        output = \
'''Трассировка маршрута к 87.240.129.133 с максимальным числом прыжков 30

  1  192.168.0.107  сообщает: Заданный узел недоступен.

 Трассировка завершена.'''
        self.assertRaises(
            ValueError,
            trace_as.parse_tracert_result,
            '87.240.129.133', output)


if __name__=='__main__':
    unittest.main()
