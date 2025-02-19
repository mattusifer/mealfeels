FROM python:3-alpine

RUN apk add build-base libpq-dev

RUN pip install --upgrade pip gunicorn

WORKDIR /app
ENV PYTHONPATH=/app

ADD ./pyproject.toml ./entrypoint.sh ./
RUN cd /app && pip install .

ADD ./mealfeels ./mealfeels

CMD ["/bin/sh", "entrypoint.sh"]
