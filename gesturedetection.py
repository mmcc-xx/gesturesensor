import config
import requests
import cv2
import numpy as np
import urllib
import time
import json
import gesturemodelfunctions
import gc
import contextlib


def pubinitial(cameraname):
    topic = config.config['gesture']['topic'] + "/" + cameraname
    payload = {'person': '', 'gesture': ''}
    print("Publishing initial state for: " + cameraname)
    ret = config.client.publish(topic, json.dumps(payload), retain=True)
    config.sentpayload[cameraname] = payload


def pubresults(cameraname, name, gesture):
    topic = config.config['gesture']['topic'] + "/" + cameraname
    payload = {'person': name, 'gesture': gesture}
    if config.sentpayload[cameraname] != payload:
        print("publishing to " + topic)
        print("Payload: " + str(payload))
        ret = config.client.publish(topic, json.dumps(payload), retain=True)
        config.sentpayload[cameraname] = payload


def getmatches(cameraname):
    # do face recognition on the latest image from frigate
    url = "http://" + config.config['double-take']['host'] + ":" + \
          str(config.config['double-take']['port']) + \
          "/api/recognize?url=http://" + config.config['frigate']['host'] + ":" + \
          str(config.config['frigate']['port']) + "/api/" + cameraname + \
          "/latest.jpg&attempts=1&camera=" + cameraname
    response = requests.get(url)
    output = response.json()
    response.close()
    return output


def getlatestimg(cameraname):
    url = "http://" + config.config['frigate']['host'] + ":" + str(config.config['frigate']['port']) + \
          "/api/" + cameraname + "/latest.jpg"

    with contextlib.closing(urllib.request.urlopen(url)) as req:
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)

    img = cv2.imdecode(arr, -1)
    return img


def lookforhands():
    # publish to the availablility topic with retain turned on
    # HA seems to need this to keep the sensor from going "unavailable"
    print("Publishing availability")
    topic = config.config['gesture']['topic'] + "/" + 'availability'
    payload = "online"
    ret = config.client.publish(topic, payload, retain=True)
    topic = config.config['gesture']['topic'] + "/" + 'availability2'
    payload = "online"
    ret = config.client.publish(topic, payload, retain=True)

    # outputnum = 0
    # publish payload with no name or gestures for each camera
    for camera in config.config['frigate']['cameras']:
        pubinitial(camera)

    while(True):
        for cameraname in config.numpersons:
            numcamerapeople = config.numpersons[cameraname]
            topic = config.config['gesture']['topic'] + "/" + cameraname

            # if there are people in front a camera
            if numcamerapeople > 0:

                matches = getmatches(cameraname)
                nummatches = int(matches['counts']['match'])

                if nummatches > 0:
                    gesture = ""

                    # find the largest match
                    biggestmatchsize = 0
                    for match in matches['matches']:
                        matchsize = match['box']['width'] * match['box']['height']
                        if matchsize > biggestmatchsize:
                            biggestmatchsize = matchsize
                            biggestmatch = match

                    # get image
                    img = getlatestimg(cameraname)
                    gesture = gesturemodelfunctions.gesturemodelmatch(img)
                    pubresults(cameraname, biggestmatch['name'], gesture)

                if nummatches == 0:
                    pubresults(cameraname, '', '')

            elif numcamerapeople == 0:
                pubresults(cameraname, '', '')

        gc.collect()
        time.sleep(0.5)
