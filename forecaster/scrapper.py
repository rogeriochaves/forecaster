import parser
import db
import requests
import psycopg2
import psycopg2.extras
import os
import sentry_sdk
from prometheus_client import CollectorRegistry, Counter, push_to_gateway

APP_ENV = os.environ.get('APP_ENV', 'dev')

CITY_CODES = {
    'Amsterdam': 'a0a48c0f8630d7e60cc5d03bf2dc2d039cad87e8dfdb8fc476a43473a6ff7e17',
    'Rio de Janeiro': '632c8273f5780465f4ef76feedd03a86dd5019a79a49165387428e1b8083caae',
    'Porto Alegre': '02497c1d67234f59ca3948f6a3361bfe5ebd55a13098b72e30391e48ce83be28',
    'Barra Mansa': '14a69e18784b4275be2e05bc6436f00e12595a8d239d122955a3dc2aba5408a0',
    'Krasnoyarsk': 'bcac3a08a51c90ff7e3fb94c1bd1b4b444b183142d7602044b094dd259853913',
    'Cairo': '2baa93f2531b18395e9b0062c11ffee82838615b3ac6141394235eb734bac64d',
}

if APP_ENV == 'prod':
    sentry_sdk.init(
        "https://a510c31a6fcb4ed4b84cba4b8064372d@o378045.ingest.sentry.io/5735160",
        traces_sample_rate=1.0
    )

registry = CollectorRegistry()
counter = Counter('scrapped_forecasts',
                  'Amount of forecasts scrapped', registry=registry)


def run():
    db.create_tables()
    scrap_city('Amsterdam')
    scrap_city('Rio de Janeiro')
    scrap_city('Porto Alegre')
    scrap_city('Barra Mansa')
    scrap_city('Krasnoyarsk')
    scrap_city('Cairo')

    if APP_ENV == 'prod':
        push_to_gateway('localhost:9091', job='scrapper.py', registry=registry)

    print("Done!")


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
        values.append((city, forecast['type'], forecast['datetime'],
                      forecast['summary'], forecast['precipitation'],
                      forecast.get('temperature'), forecast.get('max'),
                      forecast.get('min')))

    conn = db.connect()
    cur = conn.cursor()

    psycopg2.extras.execute_values(cur,
                                   "INSERT INTO Forecasts (city, type, datetime, summary, precipitation, temperature, max, min) VALUES %s",
                                   values
                                   )

    conn.commit()
    conn.close()


if __name__ == '__main__':
    run()
