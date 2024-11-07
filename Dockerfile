FROM python:3.11-slim

WORKDIR /app

COPY kotiki/entrypoints .

RUN pip install .

CMD ["python", "./main.py", "api"]
