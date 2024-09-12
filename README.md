# goodwe-prometheus-exporter
Exporter for prometheus to export metrics from GoodWe Inverter

</br>

This exporter should be working on GoodWe ET, EH, BT, BH, ES, EM, BP, DT, MS, and D-NS families of inverters. It may work on other inverters as well, as long as they listen on UDP port 8899 and respond to one of supported communication protocols. 
The inverters communicate via UDP protocol, by default running on port 8899. They use a native 'AA55' protocol and (some models) ModBus protocol. ET inverters support both protocols, some inverters may not support both of them.

(If you can't communicate with the inverter despite your model is listed above, it is possible you have old ARM firmware version. You should ask manufacturer support to upgrade your ARM firmware (not just inverter firmware) to be able to communicate with the inveter via UDP.)

more info about the python goodwe library: https://github.com/marcelblijleven/goodwe

</br>

### Pre-requisites
1. Configured inverter:
Inverter must be connected to a 2.4GHz wifi network (if you have a wifi module)
If not, you can configure it following:</br>
  1.1 Connect to a wifi network called `Solar-Wifi`. The default login is `admin` and password `admin`</br>
	note:  default password is sometimes `12345678`</br>
  1.2 Open your browser and go to http://10.10.100.253 or http://10.10.100.254</br>
  1.3 enter `admin` as username, and `admin` as password</br>
  1.4 Click `Start setup`, and select router's SSID (must be a 2.4GHz network) and it's password</br>
  1.5 click `complete` to finish the setup process</br>
</br>

2. Installed python (tested with python 3.8, 3.9, 3.10):

for Ubuntu:
```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.8 python3.8-dev python3.8-distutils python3.8-venv
```

for RHEL/CentOS:
```
yum install python3.8
```

check:
```
python3.8 --version
```

</br>


3. installed required  modules for python:
```
python -m pip install asyncio prometheus_client goodwe
```
</br>

### How to get the IP Address of the inverter
*note: the inverter must be on the same network*

To get the IP adress of the inverter, run:
```
python scripts/inverter_scan.py
```

you will see something like:</br> 
`Located inverter at IP: 192.168.2.35, mac: 289C6E05xxxx, name: Solar-WiFi222W0782`
</br>

### How to get test data

Edit the file `scripts/get-inverter-data.py` and on the line #7 add the IP address of the inverter
then run it with:
```
python scripts/get-inverter-data.py
```

and you should get all the data your inverter is exposing

</br></br>

## For standalone installation

check that you have:
- installed python
- installed goodwe modules
(see [Pre-requisites](https://github.com/gustonator/goodwe-prometheus-exporter#Pre-requisites) )
</br>

### Run/test

To test, start the exporter with minimal configuration:
```
python src/exporter.py --port <desired port> --interval <interval (s)> --inverter <inverterIP>

ie.
python src/exporter.py --port 8787 --interval 30 --inverter 192.168.2.35
```
(for more settings, see [Supported parameters](https://github.com/gustonator/goodwe-prometheus-exporter#supported-parameters))

</br>

now you can call it via curl (from another terminal) to see, if it exports some metrics:
(run in a new tab)
```
curl http://127.0.0.1:8787
```

</br>

to show help, just run the script with a `--help` parameter:
```
python src/exporter.py --help
```

</br>

if everything is OK, you can set up the script as a service:
For Ubuntu:
<documentation for debian system will follow>
</br>


## For Docker Installation

check that you have:
- installed python (need for the script to get the IP adress)(see [Pre-requisites](https://github.com/gustonator/goodwe-prometheus-exporter#Pre-requisites))
- Installed docker compose ([Docker compose installation](https://docs.docker.com.zh.xy2401.com/v17.12/compose/install/))
</br>

### Build the image
To build the image, just go to the root folder (where the Dockerfile is) and run:
```
docker build -t goodwe-exporter:1.4.5 .
```

### Install/Run
1. edit the docker-compose.yml file and put there the correct inverter IP. (other values are optional)
	- To get the IP address, see section "How to get the IP Address of the inverter"

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

4. check via curl to see,if exporter works metrics. use the IP address from step 3.
```
curl http://<IP>:8787
```
</br>

### Supported parameters

`--inverter <inverterIP>`	- [required] IP address of the inverter. To get the IP Address, see section [How to get the inverter IP address](https://github.com/gustonator/goodwe-prometheus-exporter#how-to-get-the-ip-address-of-the-inverter). </br>
`--port <desired port>`		- [optional][default: 8787] port, on which the exporter should expose the metrics</br>
`--interval <seconds>`		- [optional][default: 30] interval between scrapings (in seconds).</br>
`--energy-price <value>` 	- [optional][default: 0] energy price per kwh (in eur). If '--scrape-spot-price' is set to true, '--energy-price' value is ignored</br>
`--PVpower <value>`		- [optional][default: 5670] maximum power in Watts of your PV you can generate (ie. 5670 = 5.67 KW)</br>
`--scrape-spot-price <bool>`	- [optional][default: False] True/False, if the exporter should scrape spot price from https://www.ote-cr.cz. If it's set to 'True', exporter will set the scraped spot price as the energy price (--energy-price is ignored)</br>
`--spot-scrape-interval <minutes>` - [optional][default: 30] (in minutes) scrape interval of spot prices. If you set it too low, ote-cr.cz will block your requests</br></br>


