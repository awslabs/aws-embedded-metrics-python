FROM public.ecr.aws/docker/library/python:3.12-slim

RUN mkdir /app
WORKDIR /app

ADD canary.py .
ADD start.sh .
RUN python3 -m venv ./venv
ADD venv/lib/python3.12/site-packages /app/venv/lib/python3.12/site-packages

CMD [ "./start.sh" ]