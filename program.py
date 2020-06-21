#! /usr/bin/python
# program.py
import ais as ai
import time as tm


def decode_ais(message):
    try:
        ais_data = ai.decod_ais(message)
        ais_format = ai.format_ais(ais_data)
        return ais_format
    except ai.UnrecognizedNMEAMessageError as e:
        pass
    except ai.BadChecksumError as e:
        pass
    except Exception as e:
        pass
    return None



def make_json_dict(decoder_id, network_id):
    json_dict = ai.AISdict()
    json_dict.add('decoder_id', decoder_id)
    json_dict.add('network_id', network_id)
    return json_dict


def make_ship_dict(ship_data):
    ship_dict = ai.AISdict()
    location_ship_dict = ai.AISdict()

    location_ship_dict.add('latitude', ship_data['lat'])
    location_ship_dict.add('longitude', ship_data['lon'])
    ship_dict.add('location', location_ship_dict)
    if 'course' in ship_data:
        ship_dict.add('course', ship_data['course'])
    return ship_dict


def main():
    serial = ai.AISserial('/dev/ttyS0')
    ais_file = ai.AISfile('/home/pi/ais-decoder/outputfile.json')
    json = ai.AISjson('http://145.24.222.86:90/boat')
    json_dict = make_json_dict(1, 'localhost')
    ships_list = []

    print("Starting")
    while True:
        ships_dict = ai.AISdict()
        with open(r"/home/pi/ais-decoder/aismsg.nmea", 'w') as file:
            t_end = tm.time() + 10
            while tm.time() < t_end:
                message = serial.read_serial()
                file.write(message)
                file.write("\n")
                message = None

        tm.sleep(.1)

        with open(r"/home/pi/ais-decoder/aismsg.nmea", 'r') as file:
            for line in file:
                message = line.rstrip("\n")
                ship_data = decode_ais(message)
                if all(key in ship_data for key in ('mmsi', 'lat', 'lon')):
                    ships_dict.add(ship_data['mmsi'], make_ship_dict(ship_data))

                message = ship_data = None

        ships_list.append(ships_dict.copy())
        json_dict.add('ships', ships_list)
        tm.sleep(.1)
        js_data = json.post_data(json_dict)
        ais_file.write_data(js_data)
	ships_dict = {}
        ships_list = []

if __name__ == '__main__':
    main()
