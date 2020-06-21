#!/usr/bin/env python
# coding: latin-1
# A bunch of naive python functions to decode somes ais_data/AIVDM messages:
# try with !AIVDO,1,1,,,B00000000868rA6<H7KNswPUoP06,0*6A
# doc : http://catb.org/gpsd/AIVDM.html
#################################################################################
# HOW TO USE IT :
# msg = '!AIVDO,1,1,,,B00000000868rA6<H7KNswPUoP06,0*6A' 
# ais_data = decod_ais(msg)
# ais_format = format_ais(ais_data)
# print ais_data, ais_data['lon'], ais_format['lon']
#################################################################################
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def sign_int(s_bytes):
    # converts signed pack of bytes (as a string) to signed int
    # @param s_bytes (string) : '1001001010010010...'
    # @return (int) : signed integer 
    temp = s_bytes
    if s_bytes[0]=='1':
        l = temp.rfind('1') #find last one
        temp2=temp[:l].replace('1', '2')
        temp2=temp2.replace('0', '1')
        temp2=temp2.replace('2', '0')
        temp=temp2+temp[l:]
        return -int(temp,2)
    else:
        return int(temp,2)

def compute_checksum(msg):
    # compute the checksum of an AIS sentense by XOR every char
    # then confront it to the checksum validator
    # @param (string) msg : one AIS sentense '!AIVDO,1,1,,,B00000000868rA6<H7KNswPUoP06,0*6A'
    # @return (string) : string representation of hexadecimal sum of XORing every char bitwise
    end = msg.rfind('*') # we're gonna read from after '?'' to before '*
    start = 0
    if msg[0] in ('$','!'): start=1 # reading after '!' if it exists
    chcksum = 0
    for c in msg[start:end]: # for every char in the ais sentenses (comma included)
        chcksum = chcksum ^ ord(c) # compare them with the x-or operator '^'
    sumHex = "%x" % chcksum # makes it hexadecimal
    return sumHex.zfill(2).upper()

##############################################################################

def get_msg_type(msg):
    # read the ais sentense and return the message type
    # @param (string) msg : one AIS sentense '!AIVDM,2,1,3,B,55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53,0*3E'
    # @return (string) : the message type '!AIVDM'
    return msg.split(',')[0]

def get_payload(msg):
    # read the ais sentense and return the payload
    # @param (string) msg : one AIS sentense '!AIVDM,2,1,3,B,55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53,0*3E'
    # @return (string) : the payload '55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53'
    return msg.split(',')[5]

def get_sentence_number(msg):
    # read the ais sentense and return the number of sentenses the payload is splitted in
    # @param (string) msg : one AIS sentense '!AIVDM,2,1,3,B,55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53,0*3E'
    # @return (string) number of sentenses: '2'
    return msg.split(',')[1]

def get_sentence_count(msg):
    # read the ais sentense and return the number of the sentense
    # @param (string) msg : one AIS sentense '!AIVDM,2,1,3,B,55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53,0*3E'
    # @return (string) the number of the current: '1'
    return msg.split(',')[2]

def get_checksum(msg):
    # read the ais sentense and return the number of the sentense
    # @param (string) msg : one AIS sentense '!AIVDM,2,1,3,B,55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53,0*3E'
    # @return (string) checksum validator: '3E'
    return msg.split('*')[-1]

##############################################################################

def decod_payload(payload):
    # convert the payload from ASCII char to their 6-bits representation for every char
    # doc : http://catb.org/gpsd/AIVDM.html#_aivdm_aivdo_payload_armoring
    # @param (string) payload : '177KQ' up to 82 chars
    # @return (string) data :  '000001000111000111011011100001'
    data = ''
    for i in range(len(payload)):
        char = ord(payload[i])-48
        if char>40:
            char = char -8
        bit = '{0:b}'.format(char)
        bit = bit.zfill(6) # makes it a full 6 bits
        data = data + bit
    return data

def decod_6bits_ascii(bits):
    # decode 6bits into an ascii char, with respect to the 6bits ascii table
    # doc : http://catb.org/gpsd/AIVDM.html#_ais_payload_data_types
    # @param (string) bits : '101010'
    # @return (char) a ascii charater : '*'
    letter = int(bits,2)
    if letter < 32:
	letter+=64
    return chr(letter)

def decod_str(data):
    # decode a string of bits to an ascii one with respect to the 6bits ascii table
    # doc : http://catb.org/gpsd/AIVDM.html#_ais_payload_data_types
    # @param (string) data : a string of bits  '000001000001000001'
    # @return (string) a string of bits : 'AAA'
    name = ''
    for k in range(len(data)//6):
        letter = decod_6bits_ascii(data[6*k:6*(k+1)])
        if letter != '@':
            name += letter
    return name.rstrip()


def is_auxiliary_craft(mmsi):
    return mmsi//10000000 == 98


def decod_data(data):
    # decode AIS payload and return a dictionary with key:value
    # doc : http://catb.org/gpsd/AIVDM.html
    # @param (string) data : '11110011000101....' by pack of 6 bits
    # @return (dict) ais_data : {'type':18, etc...}
    type_nb = int(data[0:6],2)

    def decod_1(data): # Message types 1,2,3
        ais_data                    = {'type':int(data[0:6],2)}
        ais_data['mmsi']            = int(data[8:38],2)
        ais_data['lon']             = sign_int(data[61:89]) / 600000.0
        ais_data['lat']             = sign_int(data[89:116]) / 600000.0
        ais_data['course']         = int(data[116:128],2) * 0.1

        return ais_data

    def decod_4(data):
        ais_data                    = {'type':int(data[0:6],2)}
        ais_data['mmsi']            = int(data[8:38],2)
        ais_data['lon']             = sign_int(data[79:107]) / 600000.0
        ais_data['lat']             = sign_int(data[107:134]) / 600000.0

        return ais_data

    def decod_5(data):
        ais_data                    = {'type':int(data[0:6],2)}
        ais_data['mmsi']            = int(data[8:38],2)
        ais_data['shipname']        = decod_str(data[112:232])

        return ais_data

    def decod_18(data):
        ais_data                    = {'type':int(data[0:6],2)}
        ais_data['mmsi']            = int(data[8:38],2)
        ais_data['lon']             = sign_int(data[57:85])/600000.0
        ais_data['lat']             = sign_int(data[85:112])/600000.0
        ais_data['course']         = int(data[112:124],2)*0.1

        return ais_data

    def decod_24(data):
        ais_data                    = {'type':int(data[0:6],2)}
        ais_data['mmsi']            = int(data[8:38],2)
        ais_data['partno']          = int(data[38:40],2)
        if not(ais_data['partno']):
            ais_data['shipname']    = decod_str(data[40:160])
        else:
            ais_data['shiptype']    = int(data[40:48],2)
            ais_data['vendorname']  = decod_str(data[48:90]) #Older models. might be garbage
        return ais_data

    decod_type = {                              # list of the ais message type we can decode
       0  : None,       1  : decod_1,   2  : decod_1,
       3  : decod_1,    4  : decod_4,   5  : decod_5,
       6  : None,	7  : None,   	8  : None,
       9  : None,    	10 : None,  	11 : None,
       12 : None,   	13 : None,   	14 : None,
       15 : None,   	16 : None,  	17 : None,
       18 : decod_18,   19 : None,  	21 : None,
       22 : None,   	23 : None,  	24 : decod_24,
       25 : None,   	26 : None,      27 : None
    }
    try:
        ais_data = decod_type[type_nb](data)    # try to decode the sentense without assumption of its type
    except (KeyError):                                     # if it fails, like a type 16 message, execute following code
        logger.info("Cannot decode message type "+str(type_nb))
        ais_data = {'type':type_nb}
    except:
        raise                                  # raise will raise the last error (WrongKey) and crash the script
    return ais_data

globPayload = '' # in case of multi-lines sentenses, declare global var to store previous payload
def decod_ais(msg):
    """
    decode AIS messages, AIVDM/AIVDO sentences:
    if the message is split to several lines, return a dict with 'none' key as 'empty' value
    if the checksum doesn't correspond, raise an error
    :param msg: (string) one AIS sentence  '!AIVDO,1,1,,,B00000000868rA6<H7KNswPUoP06,0*6A'
    :return: (dict) ais_data : {'type':18, etc...}
    """
    if msg == '':
        return None
    message_type = get_msg_type(msg)
    if not(message_type =='!AIVDM' or message_type == '!AIVDO'):
        raise UnrecognizedNMEAMessageError(message_type)
    payload = get_payload(msg)
    s_size  = get_sentence_number(msg)
    s_count = get_sentence_count(msg)


    if (compute_checksum(msg) != get_checksum(msg)):
        logger.error('Checksum not valid (' + str(compute_checksum(msg)) + '!=' + str(
            get_checksum(msg)) + '), message is broken/corrupted')
        raise BadChecksumError()


    if s_size != '1' :                          # usefull only if multi-line sentences.
        global globPayload
        if (globPayload=='' and int(s_count) > 1):
            return {'none': 'empty'}            # This is not the first message and the main payload is empty
        if s_size != s_count:                   # if this isn't the last messages
            globPayload = globPayload + payload # append the current payload to the main payload
            return {'none':'empty'}
        else:
            payload = globPayload + payload     # append the last payload
            globPayload = ''                    # reset the global var for future messages

    data = decod_payload(payload)
    ais_data = decod_data(data)
    return ais_data

##############################################################################

def format_lat(lat):
    return float(lat)

def format_lon(lon):
    return float(lon)

def format_course(course):
    return 'N/A' if course == 3600 else course #with leading zeroes

def format_speed(speed):
    if speed == 1023:
        return 'N/A'
    elif speed == 1022:
        return ' > 102 knots'
    elif speed == 0:
        return "0 knots"
    else:
        return "{0:.1f} knots".format(speed*0.1)

def format_heading(heading):
    return 'N/A' if heading == 511 else "{:3.1f}°".format(heading).zfill(6) #with leading zeroes

def format_month(month):
    return 'N/A' if month == 0 else month

def format_day(day):
    return 'N/A' if day == 0 else day

def format_hour(hour):
    return 'N/A' if hour == 24 else hour

def format_minute(minute):
    return 'N/A' if minute == 60 else minute

def format_second(second):
    if second == 60:
        return 'N/A'
    elif second == 61:
        return 'manual mode'
    elif second == 62:
        return 'EPFS in estimated mode'
    elif second == 63:
        return 'PS inoperative'
    else:
        return second

def format_cs(cs):
    return 'Class B SOTDMA' if cs == '0' else 'Class B CS'

def format_display(display):
    return 'N/A' if display == '0' else 'Display available'

def format_dsc(dsc):
    if dsc == '1':
      return 'VHF voice radio with DSC capability'

def format_band(band):
    if band == '1':
        return 'Can use any frequency of the marine channel'

def format_msg22(msg22):
    if msg22 == '1':
        return 'Accepts channel assignment via Type 22 Message'

def format_assigned(assigned):
    if assigned == '0':
        return 'Autonomous mode'

def format_dte(dte):
    return 'Data terminal ready' if dte == '0' else 'Data terminal N/A'

def format_epfd(epfd):
    epfd_types = [  'Undefined',
                    'GPS',
                    'GLONASS',
                    'GPS/GLONASS',
                    'Loran-C',
                    'Chayka',
                    'Integrated',
                    'Surveyed',
                    'Galileo',
                    'Undefined',
                    'Undefined',
                    'Undefined',
                    'Undefined',
                    'Undefined',
                    'Undefined',
                    'Undefined']
    return epfd_types[epfd]


def format_shiptype(shiptype):
    shiptype_list = [
    "Not available",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Reserved for future use",
    "Wing in ground (WIG) - all ships of this type",
    "Wing in ground (WIG) - Hazardous category A",
    "Wing in ground (WIG) - Hazardous category B",
    "Wing in ground (WIG) - Hazardous category C",
    "Wing in ground (WIG) - Hazardous category D",
    "Wing in ground (WIG) - Reserved for future use",
    "Wing in ground (WIG) - Reserved for future use",
    "Wing in ground (WIG) - Reserved for future use",
    "Wing in ground (WIG) - Reserved for future use",
    "Wing in ground (WIG) - Reserved for future use",
    "Fishing",
    "Towing",
    "Towing: length exceeds 200m or breadth exceeds 25m",
    "Dredging or underwater ops",
    "Diving ops",
    "Military ops",
    "Sailing",
    "Pleasure Craft",
    "Reserved",
    "Reserved",
    "High speed craft (HSC) - all ships of this type",
    "High speed craft (HSC) - Hazardous category A",
    "High speed craft (HSC) - Hazardous category B",
    "High speed craft (HSC) - Hazardous category C",
    "High speed craft (HSC) - Hazardous category D",
    "High speed craft (HSC) - Reserved for future use",
    "High speed craft (HSC) - Reserved for future use",
    "High speed craft (HSC) - Reserved for future use",
    "High speed craft (HSC) - Reserved for future use",
    "High speed craft (HSC) - No additional information",
    "Pilot Vessel1",
    "Search and Rescue vessel",
    "Tug",
    "Port Tender",
    "Anti-pollution equipment",
    "Law Enforcement",
    "Spare - Local Vessel",
    "Spare - Local Vessel",
    "Medical Transport",
    "Ship according to RR Resolution No. 18",
    "Passenger - all ships of this type",
    "Passenger - Hazardous category A",
    "Passenger - Hazardous category B",
    "Passenger - Hazardous category C",
    "Passenger - Hazardous category D",
    "Passenger - Reserved for future use",
    "Passenger - Reserved for future use",
    "Passenger - Reserved for future use",
    "Passenger - Reserved for future use",
    "Passenger - No additional information",
    "Cargo - all ships of this type",
    "Cargo - Hazardous category A",
    "Cargo - Hazardous category B",
    "Cargo - Hazardous category C",
    "Cargo - Hazardous category D",
    "Cargo - Reserved for future use",
    "Cargo - Reserved for future use",
    "Cargo - Reserved for future use",
    "Cargo - Reserved for future use",
    "Cargo - No additional information",
    "Tanker - all ships of this type",
    "Tanker - Hazardous category A",
    "Tanker - Hazardous category B1",
    "Tanker - Hazardous category C1",
    "Tanker - Hazardous category D1",
    "Tanker - Reserved for future use",
    "Tanker - Reserved for future use",
    "Tanker - Reserved for future use",
    "Tanker - Reserved for future use",
    "Tanker - No additional information",
    "Other Type - all ships of this type",
    "Other Type - Hazardous category A",
    "Other Type - Hazardous category B",
    "Other Type - Hazardous category C",
    "Other Type - Hazardous category D",
    "Other Type - Reserved for future use",
    "Other Type - Reserved for future use",
    "Other Type - Reserved for future use",
    "Other Type - Reserved for future use",
    "Other Type - no additional information"
    ]
    return shiptype_list[shiptype]

def format_stationtype(stationtype):
    stationtype_list = [
        "All types of mobiles (default)",
        "Reserved for future use",
        "All types of Class B mobile stations",
        "SAR airborne mobile station",
        "Aid to Navigation station",
        "Class B shipborne mobile station (IEC62287 only)",
        "Regional use and inland waterways",
        "Reserved for future use"
    ]
    return stationtype_list[stationtype]

def format_turn(rot):
    if rot >= 1 and rot <= 126:
        return "{0:.1f}° Right".format((rot/4.733)**2)
    elif rot >= -126 and rot <= -1:
        return "{0:.1f}° Left".format((rot/4.733)**2)
    elif rot==127:
        return '> 5°/30sec Right (No TI available)'
    elif rot == -127:
        return '> 5°/30sec Left (No TI available)'
    return 'N/A'

def format_status(status):
    status_list = [
        "Under way using engine",
        "At anchor",
        "Not under command",
        "Restricted manoeuverability",
        "Constrained by her draught",
        "Moored",
        "Aground",
        "Engaged in Fishing",
        "Under way sailing",
        "Reserved for future amendment of Navigational Status for HSC",
        "Reserved for future amendment of Navigational Status for WIG",
        "Reserved for future use",
        "Reserved for future use",
        "Reserved for future use",
        "AIS-SART is active",
        "Not defined (default)",
    ]
    return status_list[status]

def format_aid_type(aid_type):
    aid_type_list = [
        "Default, Type of Aid to Navigation not specified",
        "Reference point",
        "RACON (radar transponder marking a navigation hazard)",
        "Fixed structure off shore, such as oil platforms, wind farms, rigs. (Note: This code should identify an obstruction that is fitted with an Aid-to-Navigation AIS station.)",
        "Spare, Reserved for future use",
        "Light, without sectors",
        "Light, with sectors",
        "Leading Light Front",
        "Leading Light Rear",
        "Beacon, Cardinal N",
        "Beacon, Cardinal E",
        "Beacon, Cardinal S",
        "Beacon, Cardinal W",
        "Beacon, Port hand",
        "Beacon, Starboard hand",
        "Beacon, Preferred Channel port hand",
        "Beacon, Preferred Channel starboard hand",
        "Beacon, Isolated danger",
        "Beacon, Safe water",
        "Beacon, Special mark",
        "Cardinal Mark N",
        "Cardinal Mark E",
        "Cardinal Mark S",
        "Cardinal Mark W",
        "Port hand Mark",
        "Starboard hand Mark",
        "Preferred Channel Port hand",
        "Preferred Channel Starboard hand",
        "Isolated danger",
        "Safe Water",
        "Special Mark",
        "Light Vessel / LANBY / Rigs",
    ]
    return aid_type_list[aid_type]

format_list = {#list of all the key that can be formatted
              'lat'         : format_lat,
              'lon'         : format_lon,
              'course'     : format_course,
              'stationtype' : format_stationtype,
              'shiptype'    : format_shiptype,
              }

def format_ais(ais_base):
    """
    format the ais_data database to a more user-friendly display
    :param ais_base: (dict) the ais_data base to format
    :return: (dict) ais_format : a dictionary with the same kay as ais_data but other value,
            None if ais_base is None
    """
    if (ais_base == None):
        return None
    ais_format = ais_base.copy()



    for key in list(ais_base.keys()):                                 #for every key we have
        if key in format_list:                            #if we can format it
            ais_format[key] = format_list[key](ais_format[key]) #format it
            
    return ais_format

class UnrecognizedNMEAMessageError(Exception):
    pass

class BadChecksumError(Exception):
    pass




##############################################################################
