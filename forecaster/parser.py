from bs4 import BeautifulSoup
from yyyy_mm_dd import *


def test_id(testId):
    return {"data-testid": testId}


def extract_10_day_forecast(html, today=today()):
    soup = BeautifulSoup(html, features='lxml')
    daily_forecast = soup.find(attrs=test_id("DailyForecast"))
    summaries = daily_forecast.find_all("summary")

    date = today
    result = []
    for summary in summaries:
        item = extract_day_forecast(summary, date)
        date = move_yyyy_mm_dd(date, 1)
        result.append(item)

    return result


def extract_day_forecast(summary, date):
    item = {
        "date": date,
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
