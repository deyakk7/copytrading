FROM python:3.10-alpine3.18

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /trading_app

COPY requirements.txt /trading_app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /trading_app/

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:5050"]
