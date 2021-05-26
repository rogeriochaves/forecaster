FROM python:3.7

RUN apt-get update && apt-get install -y cron

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# https://stackoverflow.com/questions/37458287/how-to-run-a-cron-job-inside-a-docker-container
RUN crontab cronfile

# https://stackoverflow.com/questions/27771781/how-can-i-access-docker-set-environment-variables-from-a-cron-job
CMD (printenv | grep -v "no_proxy" >> /etc/environment) && cron -f -L 15
