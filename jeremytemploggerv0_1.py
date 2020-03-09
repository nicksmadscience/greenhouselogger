#!/usr/bin/env python3

# roffle
import RPi.GPIO as GPIO
import dht11
import time
import datetime
import csv
from threading import Thread
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse as urlparse

# initialize GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)


instance0 = dht11.DHT11(pin=14)
instance1 = dht11.DHT11(pin=15)

data = {"temp0": -1.0, "humid0": -1.0, "temp1": -1.0, "humid1": -1.0}

PORT_NUMBER = 8001


# This class will handles any incoming request from
# the browser
class MyHandler(BaseHTTPRequestHandler):
    # Handler for the GET requests
    def do_GET(self):
        global data
        try:
            elements = self.path.split('/')
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write("Bad request! %s" % e)
            return

        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # Send the html message
            with open("index.html", "rb") as index:
                self.wfile.write(index.read())
            return
        elif self.path == "/temp":
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # Send the html message
            self.wfile.write(json.dumps(data))
        elif self.path == "/quick":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Send the html message
            # self.wfile.write(json.dumps(data))
            self.wfile.write("""<html><head><title>Temp</title></head><body>
                <h1>temp0: """ + str(data["temp0"]) + """</h1>
                <h1>humid0: """ + str(data["humid0"]) + """</h1>
                <h1>temp1: """ + str(data["temp1"]) + """</h1>
                <h1>humid1: """ + str(data["humid1"]) + """</h1>
                </body></html>
                """)
            return
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # Send the html message
            self.wfile.write("Unrecognized path!")
            return


server = HTTPServer(('', PORT_NUMBER), MyHandler)


# this is supposed to fix the "Address already in use" error (but probably won't)
# update (like eleven months later): no, of course it doesn't.
def server_bind(self):
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    HTTPServer.server_bind(self)


def webserver():
    global server
    try:
        # Create a web server and define the handler to manage the
        # incoming request
        setattr(HTTPServer, 'allow_reuse_address', 0)
        
        print('navigate your browser to http://localhost:', PORT_NUMBER)
        
        # Wait forever for incoming http requests
        server.serve_forever()

    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
    except Exception as e:
        errorHandler("Show-stopper", "Error starting the webserver! " + str(e) + str(e.args))
    finally:
        try:
            server.socket.close()
        except Exception as e:
            print(e)
            pass


webserverThread = Thread(target=webserver)
webserverThread.daemon = True
webserverThread.start()

try:
    while True:
        result0 = instance0.read()
        result1 = instance1.read()

        result0_isvalid = False
        result1_isvalid = False

        if result0.is_valid():
            print("TEMP0 (close)")
            print("Last valid input: " + str(datetime.datetime.now()))

            print("Temperature: %-3.1f C" % result0.temperature)
            print("Humidity: %-3.1f %%" % result0.humidity)
            print(type(result0.temperature))
            print(type(result0.humidity))
            result0_isvalid = True

        if result1.is_valid():
            print("TEMP1 (far)")
            print("Last valid input: " + str(datetime.datetime.now()))

            print("Temperature: %-3.1f C" % result1.temperature)
            print("Humidity: %-3.1f %%" % result1.humidity)
            result1_isvalid = True

        if result0_isvalid and result1_isvalid:
            data["temp0"] = result0.temperature
            data["humid0"] = result0.humidity
            data["temp1"] = result1.temperature
            data["humid1"] = result1.humidity

            print("logging temperature!!")
            with open('jeremydata.csv', 'a') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=',',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow([str(datetime.datetime.now()), result0.temperature, result0.humidity,
                                     result1.temperature, result1.humidity])

        time.sleep(6)
        print("\n\n")


except KeyboardInterrupt:
    print("Cleanup")
    GPIO.cleanup()
