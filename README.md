# goodwe-prometheus-exporter
Exporter for prometheus to export metrics from GoodWe Inverter

</br>
tested on models:
GoodWe GW10K-ET
</br>


## For standalone installation: 

# Pre-requisites

1. Installed python 3.8

</br>

2. install required  modules for python:
```
python -m pip install goodwe asyncio prometheus_client
```
</br>

# Run/test

3. to test, start the exporter:
```
python exporter.py --port <desired port> --interval <interval (s)> --inverter <inverterIP>

ie.
python exporter.py --port 8787 --interval 30 --inverter 192.168.2.35
```
</br>

now you can call it via curl to see,if it exports some metrics:
(run in a new tab)
```
curl http://127.0.0.1:8787
```
</br>

to show help, just run the script with a `--help` parameter:
```
python exporter.py --help
```

</br>

4. if everything is OK, you can start the script as a service:
<documentation for debian system will follow>


## For Docker

# Install/Run
1. edit the docker-compose.yml file and put there the correct IP
	(port and scrape interval are optional values)

2. from command line run:
```
docker compose up -d 
```
</br>


#check

3. get IP address of the container
```
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' goodwe-exporter
```
</br>

4. check via curl to see,if exporter works metrics
```
curl http://<IP>:8787
```
</br>
</br>

## TBD

- option to disable default python metrics
