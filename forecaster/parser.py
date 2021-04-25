from bs4 import BeautifulSoup
from yyyy_mm_dd import *


def test_id(testId):
    return {"data-testid": testId}


def extract_10_day_forecast(html, today=today()):
    soup = BeautifulSoup(html, features='lxml')
    daily_forecast = soup.find(attrs=test_id("DailyForecast"))
    summaries = daily_forecast.find_all("summary")

    datetime = start_of_yyyy_mm_dd(today)
    result = []
    for summary in summaries:
        item = extract_day_forecast(summary, datetime)
        datetime = move_yyyy_mm_dd(datetime, 1)
        result.append(item)

    return result


def extract_day_forecast(summary, datetime):
    item = {
        "type": "daily",
        "datetime": datetime,
        "precipitation": "0%",
        "summary": summary.find(attrs=test_id("wxIcon")).find("span").get_text()
    }
    temperature = summary.find(attrs=test_id("detailsTemperature"))
    item["max"] = temperature.find(
        attrs=test_id("TemperatureValue")).get_text()
    item["min"] = temperature.find(attrs=test_id(
        "lowTempValue")).find("span").get_text()

    precipitation = summary.find(attrs=test_id("Precip"))
    if precipitation:
        item["precipitation"] = precipitation.find(
            attrs=test_id("PercentageValue")).get_text()

    return item


def extract_hourly_forecast(html, now=now()):
    soup = BeautifulSoup(html, features='lxml')
    daily_forecast = soup.find(attrs=test_id("HourlyForecast"))
    summaries = daily_forecast.find_all("summary")

    datetime = move_yyyy_mm_dd_hh(start_of_yyyy_mm_dd(now), hour(now))
    # if it's quarter past the hour TWC shows forecast for next hour
    if to_datetime(now).minute > 15:
        datetime = move_yyyy_mm_dd_hh(datetime, 1)
    result = []
    for summary in summaries:
        item = extract_hour_forecast(summary, datetime)
        datetime = move_yyyy_mm_dd_hh(datetime, 1)
        result.append(item)

    return result


def extract_hour_forecast(summary, datetime):
    item = {
        "type": "hourly",
        "datetime": datetime,
        "precipitation": "0%",
        "summary": summary.find(attrs=test_id("wxIcon")).find("span").get_text()
    }
    temperature = summary.find(attrs=test_id("detailsTemperature"))
    item["temperature"] = temperature.find(
        attrs=test_id("TemperatureValue")).get_text()

    precipitation = summary.find(attrs=test_id("Precip"))
    if precipitation:
        item["precipitation"] = precipitation.find(
            attrs=test_id("PercentageValue")).get_text()

    return item
