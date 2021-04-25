import unittest

import forecaster.parser as parser


def fixture(filename):
    with open("tests/fixtures/" + filename) as f:
        return f.read()


class ParserTestCase(unittest.TestCase):
    def test_extracts_10_day_forecast(self):
        result = parser.extract_10_day_forecast(
            fixture("ams-ten-day.html"), today='2021-04-25')
        self.assertEqual(result[0:2], [
            {
                'date': '2021-04-25',
                'precipitation': '0%',
                'summary': 'AM Clouds/PM Sun',
                'max': '10°',
                'min': '2°'
            },
            {
                'date': '2021-04-26',
                'precipitation': '10%',
                'summary': 'Partly Cloudy',
                'max': '11°',
                'min': '3°'
            },
        ])
