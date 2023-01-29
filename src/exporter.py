from prometheus_client import CollectorRegistry, Gauge, Counter, Info
from datetime import datetime
import prometheus_client as prometheus
import sys
import getopt
import time
import socket
import urllib.request
import asyncio
import goodwe

print("\nGOODWE DATA EXPORTER v1.0.0\n")


def checkArgs(argv):
    global EXPORTER_PORT
    global POLLING_INTERVAL
    global INVERTER_IP

    # set default values
    EXPORTER_PORT = 8787
    POLLING_INTERVAL = 30
    INVERTER_IP = ""

    # help
    arg_help = "{0} --port <exporter port [default:8787]> --interval <scrape interval (seconds) [default:30]> --inverter <inverter IP>".format(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "hp:t:i:", ["help", "port=", "interval=", "inverter="])
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

    # check if Inverter IP is set
    if not INVERTER_IP:
        print("ERROR: missing IP Address of inverter!")
        exit(1)
                


class InverterMetrics:
    def __init__(self, g, i, POLLING_INTERVAL):
        self.POLLING_INTERVAL = POLLING_INTERVAL
        self.metricsCount = 0
        self.g = g
        self.i = i
    
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
        async def fetch_inverter():
            inverter = await goodwe.connect(INVERTER_IP)
            runtime_data = await inverter.read_runtime_data()
            countID = 0

            for sensor in inverter.sensors():
                if sensor.id_ in runtime_data and type(runtime_data[sensor.id_]) == int or type(runtime_data[sensor.id_]) == float:
                    self.g[countID].set(str(runtime_data[sensor.id_]))
                    countID+=1

            self.metricsCount=len(self.g)-1

        asyncio.run(fetch_inverter())

        # print number of metrics and date and rewrites it every time
        print("number of metrics:\t\t"+str(self.metricsCount))
        print("last scrape:\t\t\t"+ str(datetime.now().strftime("%d.%m.%Y %H:%M:%S")), end='\r')
        print('\033[1A', end='\x1b[2K')



def main():
    checkArgs(sys.argv)

    print("polling interval:\t\t"+str(POLLING_INTERVAL)+"s")
    print("inverter scrape IP:\t\t"+str(INVERTER_IP))

    inverter_metrics = InverterMetrics(
        POLLING_INTERVAL=int(POLLING_INTERVAL),
        g=[],
        i=[]
    )

    # Start the server to expose metrics.
    prometheus.start_http_server(int(EXPORTER_PORT))
    print("exporter started on port:\t"+str(EXPORTER_PORT)+"\n")

    inverter_metrics.run_metrics_loop()


if __name__ == "__main__":
    main()
