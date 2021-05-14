import error_reporting
import parser
import db
import requests
import psycopg2
import psycopg2.extras
import os
import time
from prometheus_client import CollectorRegistry, Counter, push_to_gateway

APP_ENV = os.environ.get('APP_ENV', 'dev')

CITY_CODES = {
    'Amsterdam': 'a0a48c0f8630d7e60cc5d03bf2dc2d039cad87e8dfdb8fc476a43473a6ff7e17',
    'Rio de Janeiro': '632c8273f5780465f4ef76feedd03a86dd5019a79a49165387428e1b8083caae',
    'Porto Alegre': '02497c1d67234f59ca3948f6a3361bfe5ebd55a13098b72e30391e48ce83be28',
    'Barra Mansa': '14a69e18784b4275be2e05bc6436f00e12595a8d239d122955a3dc2aba5408a0',
    'Krasnoyarsk': 'bcac3a08a51c90ff7e3fb94c1bd1b4b444b183142d7602044b094dd259853913',
    'Cairo': '2baa93f2531b18395e9b0062c11ffee82838615b3ac6141394235eb734bac64d',
    'Valença': '801c966fba6db9868eeeb81c96bae2c09cf7a3c3578618559ad5be9e4f2d859a',
    'London': 'ae8230efd4bc57fdf721a02c7eb2b88c56aa6e71d73666328e33af3ea2039032132e24ae91b6a07862c5091a9d95a4b8',
    'Athens': '5892dfe2c539df7d42cdbd8f9cfda434f21f6c2a63cec329fa598d4e5aa3d584',
    'Barcelona': '0ce8d487db0a25631ee2017ddbe068bfba0de2b24de23f0b82c95863724f3a86'
}

registry = CollectorRegistry()
counter = Counter('scrapped_forecasts',
                  'Amount of forecasts scrapped', registry=registry)


def run():
    db.create_tables()
    for city in CITY_CODES.keys():
        scrap_city_try_twice(city)

    if APP_ENV == 'prod':
        push_to_gateway('localhost:9091', job='scrapper.py', registry=registry)

    print("Done!")


def scrap_city_try_twice(name):
    try:
        scrap_city(name)
    except:
        print("Scrapping city " + name + " failed, trying again in 5s")
        time.sleep(5)
        scrap_city(name)


def scrap_city(name):
    code = CITY_CODES[name]

    req = requests.get('https://weather.com/en-GB/weather/tenday/l/' + code)
    forecasts = parser.extract_10_day_forecast(req.text)
    save(name, forecasts)
    counter.inc(len(forecasts))
    print("Saved 10 day forecast for", name)

    req = requests.get(
        'https://weather.com/en-GB/weather/hourbyhour/l/' + code)
    forecasts = parser.extract_hourly_forecast(req.text)
    save(name, forecasts)
    counter.inc(len(forecasts))
    print("Saved hourly forecast for", name)


def save(city, forecasts):
    values = []
    for forecast in forecasts:
        values.append((city, forecast['type'], forecast['forecast_delta'],
                      forecast['summary'], forecast['precipitation'],
                      forecast.get('temperature'), forecast.get('max'),
                      forecast.get('min')))

    conn = db.connect()
    cur = conn.cursor()

    psycopg2.extras.execute_values(cur,
                                   "INSERT INTO Forecasts (city, type, forecast_delta, summary, precipitation, temperature, max, min) VALUES %s",
                                   values
                                   )

    conn.commit()
    conn.close()


if __name__ == '__main__':
    run()
