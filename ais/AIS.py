# AIS.py
import serial
import json
import collections
import urllib2


class AISdict(dict):
    def __init__(self):
        self = collections.OrderedDict()

    def add(self, key, value):
        self[key] = value


class AISserial():
    def __init__(self, port):
        self.se = serial.Serial(port, baudrate = 38400, bytesize = 8, parity = serial.PARITY_NONE, stopbits = 1, timeout = None, xonxoff = False, rtscts = False, dsrdtr = False)
    
    def read_serial(self):
        data_raw = ""
        if not data_raw:
            tmp = self.se.readline().decode().strip()
            if tmp:
                data_raw = tmp
        return data_raw


class AISjson():
    def __init__(self, url):
        self.request = urllib2.Request(url)
        self.request.add_header('Content-Type', 'application/json; charset=utf-8')

    def post_data(self, dictionary):
        json_data = json.dumps(dictionary)
        json_data_bytes = json_data.encode('utf-8')
        self.request.add_header('Content-Length', len(json_data_bytes))
        response = urllib2.urlopen(self.request, json_data_bytes)
        response.close()