from bs4 import BeautifulSoup
from yyyy_mm_dd import *


def test_id(testId):
    return {"data-testid": testId}


def extract_10_day_forecast(html):
    soup = BeautifulSoup(html, features='html.parser')
    daily_forecast = soup.find(attrs=test_id("DailyForecast"))
    summaries = daily_forecast.find_all("summary")

    result = []
    for delta, summary in enumerate(summaries):
        item = extract_day_forecast(summary, delta)
        result.append(item)

    return result


def extract_day_forecast(summary, delta):
    item = {
        "type": "daily",
        "forecast_delta": delta,
        "precipitation": get_precipitation(summary),
        "summary": summary.find(attrs=test_id("wxIcon")).find("span").get_text()
    }
    temperature = summary.find(attrs=test_id("detailsTemperature"))
    item["max"] = parse_temperature(temperature.find(
        attrs=test_id("TemperatureValue")))
    item["min"] = parse_temperature(temperature.find(attrs=test_id(
        "lowTempValue")).find("span"))

    return item


def extract_hourly_forecast(html, now=now()):
    soup = BeautifulSoup(html, features='html.parser')
    daily_forecast = soup.find(attrs=test_id("HourlyForecast"))
    summaries = daily_forecast.find_all("summary")

    delta = 0
    # if it's quarter past the hour TWC shows forecast for next hour
    if to_datetime(now).minute > 15:
        delta = 1
    result = []
    for summary in summaries:
        item = extract_hour_forecast(summary, delta)
        delta = delta + 1
        result.append(item)

    return result


def extract_hour_forecast(summary, delta):
    item = {
        "type": "hourly",
        "forecast_delta": delta,
        "precipitation": get_precipitation(summary),
        "summary": summary.find(attrs=test_id("wxIcon")).find("span").get_text()
    }
    temperature = summary.find(attrs=test_id("detailsTemperature"))
    item["temperature"] = parse_temperature(temperature.find(
        attrs=test_id("TemperatureValue")))

    return item


def get_precipitation(summary):
    precipitation = summary.find(attrs=test_id("Precip"))
    if precipitation:
        precipitation = precipitation.find(
            attrs=test_id("PercentageValue")).get_text()
        precipitation = int(precipitation.replace("%", ""))
        return precipitation

    return 0


def parse_temperature(node):
    temperature = node.get_text().replace("°", "")
    try:
        return int(temperature)
    except:
        return None
