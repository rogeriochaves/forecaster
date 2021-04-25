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
                'type': 'daily',
                'datetime': '2021-04-25T00:00:00',
                'precipitation': 0,
                'summary': 'AM Clouds/PM Sun',
                'max': 10,
                'min': 2
            },
            {
                'type': 'daily',
                'datetime': '2021-04-26T00:00:00',
                'precipitation': 10,
                'summary': 'Partly Cloudy',
                'max': 11,
                'min': 3
            },
        ])

    def test_extracts_hourly_forecast(self):
        result = parser.extract_hourly_forecast(
            fixture("ams-hourly.html"), now='2021-04-25T15:01:00')

        self.assertEqual(result[0:2], [
            {
                'type': 'hourly',
                'datetime': '2021-04-25T15:00:00',
                'precipitation': 0,
                'summary': 'Mostly Cloudy',
                'temperature': 10
            },
            {
                'type': 'hourly',
                'datetime': '2021-04-25T16:00:00',
                'precipitation': 0,
                'summary': 'Mostly Cloudy',
                'temperature': 10
            },
        ])
