FROM python:3.8-alpine
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY /src/exporter.py .
RUN python -m pip install --upgrade pip
RUN pip install --root-user-action=ignore --upgrade goodwe asyncio aiohttp prometheus_client 
ENTRYPOINT ["python", "exporter.py"]
