#!/usr/bin/python3
import smbus
import math
import time
from datetime import datetime
from elasticsearch import Elasticsearch
from requests.auth import HTTPBasicAuth
from elastic_settings import IP, USER, PASS

time.sleep(5)

power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

def read_byte(reg):
    return bus.read_byte_data(address, reg)

def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg+1)
    value = (h << 8) + l
    return value

def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def dist(a,b):
    return math.sqrt((a*a) + (b*b))

def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)

def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x, z))
    return math.degrees(radians)

bus = smbus.SMBus(1)
address = 0x68

bus.write_byte_data(address, power_mgmt_1, 0)

es = Elasticsearch([IP], http_auth=(USER, PASS), scheme='http', port=9200)
print(es.ping())

print('Accel')
print('--------')

while 1:
    x_out = read_word_2c(0x3b) / 16384.0
    y_out = read_word_2c(0x3d) / 16384.0
    z_out = read_word_2c(0x3f) / 16384.0
    
    
    # print('x out: ', ('%3f' % x_out))
    # print('y out: ', ('%3f' % y_out))
    # print('z out: ', ('%3f' % z_out))

    x_rotation = get_x_rotation(x_out, y_out, z_out)
    y_rotation = get_y_rotation(x_out, y_out, z_out)

    print('x rotation: ', x_rotation, ' degrees ')
    print('y rotation: ', y_rotation, ' degrees ')
    print('---------------------------------')
    doc = {
        'x_rotation': round(x_rotation, 2),
        'y_rotation': round(y_rotation, 2),
        'author': 'john dimatteo',
        'timestamp': datetime.now(),
        'tag': 'P-0120',
    }
    es.index(index='iotdata', body=doc)
    time.sleep(1)
