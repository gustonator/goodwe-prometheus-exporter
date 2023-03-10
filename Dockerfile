FROM python:3.8-alpine
WORKDIR /app
COPY /src/exporter.py .
RUN pip install --upgrade goodwe asyncio prometheus_client 
ENTRYPOINT ["python", "exporter.py"]
