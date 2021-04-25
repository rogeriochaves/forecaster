FROM python:3.7

RUN apt-get update && apt-get install -y cron

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD bash
RUN touch crontab.tmp \
    && echo '0 * * * * python /app/forecaster/scrapper.py' >> crontab.tmp \
    && crontab crontab.tmp \
    && rm -rf crontab.tmp

CMD /usr/sbin/cron -f
