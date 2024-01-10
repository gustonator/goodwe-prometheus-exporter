from prometheus_client import CollectorRegistry, Gauge, Counter, Info
from datetime import date, datetime, timedelta
from decimal import Decimal
import prometheus_client as prometheus
import xml.etree.ElementTree as ET
import traceback
import logging
import sys
import getopt
import time
import asyncio
import aiohttp
import goodwe

#logger = logging.getLogger(__name__)

print("\nGOODWE DATA EXPORTER v1.4.2\n")

QUERY = '''<?xml version="1.0" encoding="UTF-8" ?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:pub="http://www.ote-cr.cz/schema/service/public">
    <soapenv:Header/>
    <soapenv:Body>                                                                          
        <pub:GetDamPriceE>
            <pub:StartDate>{start}</pub:StartDate>
            <pub:EndDate>{end}</pub:EndDate>
            <pub:InEur>{in_eur}</pub:InEur>
        </pub:GetDamPriceE>
    </soapenv:Body>
</soapenv:Envelope>
'''
class OTEFault(Exception):
    pass

class InvalidFormat(OTEFault):
    pass


def checkArgs(argv):
    global EXPORTER_PORT
    global POLLING_INTERVAL
    global INVERTER_IP
    global ENERGY_PRICE
    global PV_POWER
    global SCRAPE_SPOT_PRICE
    global SPOT_SCRAPE_INTERVAL
    global LAST_SPOT_UPDATE

    # set default values
    EXPORTER_PORT = 8787
    POLLING_INTERVAL = 30
    ENERGY_PRICE = 0.20
    PV_POWER = 5670
    INVERTER_IP = ""
    SCRAPE_SPOT_PRICE = False
    SPOT_SCRAPE_INTERVAL = timedelta(minutes=int(30))
    LAST_SPOT_UPDATE = datetime.now() - SPOT_SCRAPE_INTERVAL

    # help
    arg_help = "\nREQUIRED PARAMETERS::\n\t-i, --inverter\n\t\tIP adress of the inverter\n\nOPTIONAL PARAMETERS:\n\t-h, --help \n\t\tShows this menu\n\t-p, --port \n\t\texporter port - on which port should the exporter expose data [default:8787]\n\t-t, --interval\n\t\tscrape interval (in seconds) [default:30] \n\t-e. --energy-price \n\t\tprice per KWh in eur [default: 0.20] \n\t-w, --PVpower \n\t\tmaximum KW your PV can produce [default:5670] \n\t-s, --scrape-spot-price \n\t\t[True/False] Set to True, for scraping  spot prices from www.ote-cr.cz [default: False] \n\t-x, --spot-scrape-interval \n\t\tscrape interval of spot prices. If you set it too low, ote-cr.cz will block your requests (in minutes) [default:30] ".format(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "hp:t:i:s:", ["help", "port=", "interval=", "inverter=", "energy-price=", "PVpower=", "scrape-spot-price=", "spot-scrape-interval="])
    except:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)
            sys.exit(2)
        elif opt in ("-p", "--port"):
            EXPORTER_PORT= arg
        elif opt in ("-t", "--interval"):
            POLLING_INTERVAL = arg
        elif opt in ("-i", "--inverter"):
            INVERTER_IP = arg
        elif opt in ("-e", "--energy-price"):
            ENERGY_PRICE = arg
        elif opt in ("-w", "--PVpower"):
            PV_POWER = arg
        elif opt in ("-s", "--scrape-spot-price"):
            SCRAPE_SPOT_PRICE = True
        elif opt in ("-x", "--spot-scrape-interval"):
            # define time for spot price scrape interval
            SPOT_SCRAPE_INTERVAL = timedelta(minutes=int(arg))
            # take defined interval so it scrapes it always the 1st time
            LAST_SPOT_UPDATE = datetime.now() - SPOT_SCRAPE_INTERVAL

    # check if Inverter IP is set
    if not INVERTER_IP:
        print("ERROR: missing IP Address of inverter!\n")
        print(arg_help)
        sys.exit(2)

class InverterMetrics:
    ELECTRICITY_PRICE_URL = 'https://www.ote-cr.cz/services/PublicDataService' #deleted "e"

    # build the query - fill the variables
    def get_query(self, start: date, end: date, in_eur: bool) -> str:
        return QUERY.format(start=start.isoformat(), end=end.isoformat(), in_eur='true' if in_eur else 'false')

    # download data from web
    async def _download(self, query: str) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://www.ote-cr.cz') as response:
                    async with session.post(self.ELECTRICITY_PRICE_URL, data=query) as response:
                        return await response.text()
        except aiohttp.ClientConnectorError as e:
            print(f"SSL error occurred: {e}")

    def parse_spot_data(self, xmlResponse):
        root = ET.fromstring(xmlResponse)
        for item in root.findall('.//{http://www.ote-cr.cz/schema/service/public}Item'):
            hour_el = item.find('{http://www.ote-cr.cz/schema/service/public}Hour')
            price_el = item.find('{http://www.ote-cr.cz/schema/service/public}Price')
            current_hour = datetime.now().hour

            if (int(hour_el.text) - 1) == current_hour:
                price_el = Decimal(price_el.text)
                price_el /= Decimal(1000) #convert MWh -> KWh
                return price_el
        
    def __init__(self, POLLING_INTERVAL,ENERGY_PRICE,PV_POWER,SCRAPE_SPOT_PRICE,SPOT_SCRAPE_INTERVAL,LAST_SPOT_UPDATE):
        self.POLLING_INTERVAL = POLLING_INTERVAL
        self.ENERGY_PRICE = ENERGY_PRICE
        self.PV_POWER = PV_POWER
        self.SCRAPE_SPOT_PRICE = SCRAPE_SPOT_PRICE
        self.SPOT_SCRAPE_INTERVAL = SPOT_SCRAPE_INTERVAL
        self.LAST_SPOT_UPDATE = LAST_SPOT_UPDATE
        self.metricsCount = 0
        self.g = []
        self.i = []

    # create placeholder for metrics in the register
    def collector_register(self):
        async def create_collector_registers():
            inverter = await goodwe.connect(INVERTER_IP)
            runtime_data = await inverter.read_runtime_data()
        
            for sensor in inverter.sensors():
                if sensor.id_ in runtime_data and type(runtime_data[sensor.id_]) == int or type(runtime_data[sensor.id_]) == float:
                    self.g.append(Gauge(sensor.id_, sensor.name))
        
                elif sensor.id_ in runtime_data and sensor.id_ != "timestamp" and type(runtime_data[sensor.id_]) != int:
                    self.i.append(Info(sensor.id_, sensor.name))

            # add additional energy-price
            self.g.append(Gauge("energy_price", "Energy price per KW"))

            # add additional PV Power
            self.g.append(Gauge("pv_total_power", "Total power in WATTS, that can be produced by PV"))
            
        asyncio.run(create_collector_registers())

    # scrape loop
    def run_metrics_loop(self):
        self.collector_register()
        while True:
            self.fetch_data()
            time.sleep(self.POLLING_INTERVAL)

    # scrape metrics in a loop and write to the prepared metrics register
    def fetch_data(self):
        self.metricsCount = 0
        
        # get spot prices
        if self.SCRAPE_SPOT_PRICE:
            now = datetime.now()
            # if the last spot price update was more that 30min ago, scrape it again
            if now - self.LAST_SPOT_UPDATE > self.SPOT_SCRAPE_INTERVAL:
                query = self.get_query(date.today(), date.today(), in_eur=True)
                xmlResponse = asyncio.run(self._download(query))
                self.ENERGY_PRICE = self.parse_spot_data(xmlResponse)
                self.LAST_SPOT_UPDATE = now 

        async def fetch_inverter():
            inverter = await goodwe.connect(INVERTER_IP)
            runtime_data = await inverter.read_runtime_data()
            countID = 0

            for sensor in inverter.sensors():
                if sensor.id_ in runtime_data and type(runtime_data[sensor.id_]) == int or type(runtime_data[sensor.id_]) == float:
                    self.g[countID].set(str(runtime_data[sensor.id_]))
                    countID+=1

            # set value for additional energy-price
            self.g[countID].set(float(self.ENERGY_PRICE))
            self.g[countID+1].set(float(PV_POWER))
            self.metricsCount=len(self.g)

        asyncio.run(fetch_inverter())

        # print number of metrics and date and rewrites it every time
        print('-------------------------------------------------------')
        if self.SCRAPE_SPOT_PRICE:
            print("energy price(spot):\t\t"+str(self.ENERGY_PRICE)+" eur/KW")
            print("last spot price scrape:\t\t"+str(self.LAST_SPOT_UPDATE))
        else:
            print("energy price (fixed):\t\t"+str(self.ENERGY_PRICE)+" eur/KW")
        print("number of metrics:\t\t"+str(self.metricsCount))
        print("last scrape:\t\t\t"+ str(datetime.now().strftime("%d.%m.%Y %H:%M:%S")))


def main():
    try:
         # Set up logging
        logging.basicConfig(filename='exporter.log', level=logging.WARNING, format='%(asctime)s %(name)-14s %(levelname)-10s %(message)s', filemode='a')

        checkArgs(sys.argv)

        print("polling interval:\t\t"+str(POLLING_INTERVAL)+"s")
        print("inverter scrape IP:\t\t"+str(INVERTER_IP))
        print("total PV power: \t\t"+str(PV_POWER)+"W")
        if SCRAPE_SPOT_PRICE:
            print("spot price scrape: \t\tEnabled")
            print("spot price scrape interval: \t"+str(SPOT_SCRAPE_INTERVAL)+" min")
        else:
            print("spot price scrape: \t\tDisabled")
            print("fixed energy price: \t\t"+str(ENERGY_PRICE)+" eur/KW")

        inverter_metrics = InverterMetrics(
            POLLING_INTERVAL=int(POLLING_INTERVAL),
            ENERGY_PRICE=ENERGY_PRICE,
            PV_POWER=PV_POWER,
            SCRAPE_SPOT_PRICE=SCRAPE_SPOT_PRICE,
            SPOT_SCRAPE_INTERVAL=SPOT_SCRAPE_INTERVAL,
            LAST_SPOT_UPDATE=LAST_SPOT_UPDATE
        )

        # Start the server to expose metrics.
        prometheus.start_http_server(int(EXPORTER_PORT))
        print("exporter started on port:\t"+str(EXPORTER_PORT)+"\n")

        inverter_metrics.run_metrics_loop()

    except KeyboardInterrupt:
        key_message='Manually interrupted by keyboard'
        print("\n"+key_message+"\n")
        logging.warning(key_message)

    except Exception  as e:
        logging.error("An error occurred: %s", e)
        traceback.print_exc()


if __name__ == "__main__":
        main()
    

