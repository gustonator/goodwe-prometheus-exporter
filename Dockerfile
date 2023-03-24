FROM python:3.8-alpine
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY /src/exporter.py .
RUN pip install --upgrade goodwe asyncio aiohttp prometheus_client 
ENTRYPOINT ["python", "exporter.py"]
