FROM python:3.7

RUN mkdir /app
WORKDIR /app

ADD canary.py .
ADD start.sh .
RUN python3 -m venv ./venv
ADD venv/lib/python3.7/site-packages /app/venv/lib/python3.7/site-packages

CMD [ "./start.sh" ]