import serial

class AISserial():
    def __init__(self):
        self.se = serial.Serial('/dev/ttyS3', baudrate = 38400, bytesize = 8, parity = serial.PARITY_NONE, stopbits = 1, timeout = None, xonxoff = False, rtscts = False, dsrdtr = False)
    
    
    def read_serial(self):
        data_raw = ""
        if not data_raw:
            tmp = self.se.readline().decode().strip()
            if tmp:
                data_raw = tmp
        return data_raw