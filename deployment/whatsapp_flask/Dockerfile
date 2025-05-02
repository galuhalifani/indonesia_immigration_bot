FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]