FROM python:3.7

RUN apt-get update && apt-get install -y cron

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

RUN (crontab -l; echo "0 * * * * /usr/local/bin/python3 /app/forecaster/scrapper.py > /proc/1/fd/1 2>/proc/1/fd/2") | crontab

CMD cron -f -L 15
