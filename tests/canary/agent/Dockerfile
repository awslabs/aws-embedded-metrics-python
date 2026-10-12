FROM public.ecr.aws/docker/library/python:3.12-slim

# Apply latest Debian security updates to clear out-of-SLA OS-package CVEs
RUN apt-get update && apt-get -y upgrade && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

ADD canary.py .
ADD start.sh .
RUN python3 -m venv ./venv
ADD venv/lib/python3.12/site-packages /app/venv/lib/python3.12/site-packages

CMD [ "./start.sh" ]