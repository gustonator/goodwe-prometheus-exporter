# goodwe-prometheus-exporter
Exporter for prometheus to export metrics from GoodWe Inverter

</br>

This exporter should be working on GoodWe ET, EH, BT, BH, ES, EM, BP, DT, MS, and D-NS families of inverters. It may work on other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication protocols. 
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

3. to test, start the exporter with minimal configuration:
```
python exporter.py --port <desired port> --interval <interval (s)> --inverter <inverterIP>

ie.
python exporter.py --port 8787 --interval 30 --inverter 192.168.2.35
```
(for more settings, see parameters below)
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
</br>


## For Docker

### Install/Run
1. edit the docker-compose.yml file and put there the correct IP
	(other values are optional)

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

### Supported parameters

`--inverter <inverterIP>`	- [required] IP address of the iverter. To get the IP Address, you can run the 'inverter_scan.py' script. </br>
`--port <desired port>`		- [optional][default: 8787] port, on which the exporter should expose the metrics</br>
`--interval <interval (s)>`	- [optional][default: 30] interval between scrapings in seconds.</br>
`--energy-price <value>` 	- [optional][default: 0.15] energy price per kwh (in eur). If '--scrape-spot-price' is set to true, '--energy-price' value is ignored</br>
`--PVpower <value>`		- [optional][default: 5670] maximum power in Watts of your PV you can generate (ie. 5670 = 5670W)</br>
`--scrape-spot-price <bool>`	- [optional][default: False] True/False, if the exporter should scrape spot price from https://www.ote-cr.cz. If it's set to 'True', exporter will set spot_price as the energy price</br>
