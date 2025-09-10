FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PORT=3000
EXPOSE 3000

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:3000", "--timeout", "120"]
