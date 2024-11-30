FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

COPY scripts/run_migrations.sh /app/
RUN chmod +x /app/run_migrations.sh

CMD ["/app/run_migrations.sh"]