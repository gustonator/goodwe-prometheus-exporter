# goodwe-prometheus-exporter
Exporter for prometheus to export metrics from GoodWe Inverter

</br>
tested on models:
GoodWe GW10K-ET
</br>

info: 
It has been reported to work on GoodWe ET, EH, BT, BH, ES, EM, BP, DT, MS, D-NS, and XS families of inverters. It may work on other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication protocols.
The inverters communicate via UDP protocol, by default running on port 8899. They use a native 'AA55' protocol and (some models) ModBus protocol. ET inverters support both protocols, some inverters may not support both of them.

(If you can't communicate with the inverter despite your model is listed above, it is possible you have old ARM firmware version. You should ask manufacturer support to upgrade your ARM firmware (not just inverter firmware) to be able to communicate with the inveter via UDP.)

more info about the python goodwe library: https://github.com/marcelblijleven/goodwe

</br>

## For standalone installation: 

### Pre-requisites

1. Installed python 3.8

</br>

2. install required  modules for python:
```
python -m pip install asyncio prometheus_client
pip install goodwe==0.2.23
```
</br>

### Run/test

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

### Install/Run
1. edit the docker-compose.yml file and put there the correct IP
	(port and scrape interval are optional values)

2. from command line run:
```
docker compose up -d 
```
</br>


### check

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
