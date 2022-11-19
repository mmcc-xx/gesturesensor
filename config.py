import yaml
import paho.mqtt.client as mqtt

config = ""
numpersons = {}
sentpayload = {}
client = mqtt.Client()

def init():
    global config
    #with open('/config/config.yml', 'r') as file:
    with open('config.yml', 'r') as file:
        config = yaml.safe_load(file)

    for camera in config['frigate']['cameras']:
        numpersons[camera] = 0
        sentpayload[camera] = ""
