FROM python:3-alpine

RUN apk add build-base libpq-dev

RUN pip install --upgrade pip gunicorn

WORKDIR /app
ENV PYTHONPATH=/app

ADD ./requirements.txt ./
RUN cd /app && pip install -r requirements.txt

ADD ./main.py ./

CMD ["gunicorn", "-b", "0.0.0.0", "-w", "1", "main:main()"]
