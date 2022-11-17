import config
import requests
import cv2
import numpy as np
import urllib
import time
import json
import gesturemodelfunctions


def lookforhands():
    # publish to the availablility topic with retain turned on
    # HA seems to need this to keep the sensor from going "unavailable"
    print("Publishing availability")
    topic = config.config['gesture']['topic'] + "/" + 'availability'
    payload = "online"
    ret = config.client.publish(topic, payload, retain=True)

    # outputnum = 0
    # publish payload with no name or gestures for each camera
    for camera in config.config['frigate']['cameras']:
        topic = config.config['gesture']['topic'] + "/" + camera
        payload = {'person': '', 'gesture': ''}
        ret = config.client.publish(topic, json.dumps(payload), retain=True)
        config.sentpayload[camera] = payload

    while(True):
        for cameraname in config.numpersons:
            numcamerapeople = config.numpersons[cameraname]
            topic = config.config['gesture']['topic'] + "/" + cameraname

            # there's a people in front a comera
            if numcamerapeople > 0:

                # do face recognition on the latest image from frigate
                url = "http://" + config.config['double-take']['host'] + ":" + \
                      str(config.config['double-take']['port']) + \
                    "/api/recognize?url=http://" + config.config['frigate']['host'] + ":" + \
                      str(config.config['frigate']['port']) + "/api/" + cameraname + \
                      "/latest.jpg&attempts=1&camera=" + cameraname
                response = requests.get(url)
                output = response.json()
                nummatches = int(output['counts']['match'])

                url = "http://" + config.config['frigate']['host'] + ":" + str(config.config['frigate']['port']) + \
                      "/api/" + cameraname + "/latest.jpg"

                #req = urllib.request.urlopen(url)
                #arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                #img = cv2.imdecode(arr, -1)
                #cv2.imwrite('output'+ str(outputnum) + '.jpg', img)
                #outputnum = outputnum + 1
                #print(output)

                if nummatches > 0:
                    gesture = ""
                    # find the largest match
                    biggestmatchsize = 0
                    for match in output['matches']:
                        matchsize = match['box']['width'] * match['box']['height']
                        if matchsize > biggestmatchsize:
                            biggestmatchsize = matchsize
                            biggestmatch = match

                    print ("Person Recognized: " + biggestmatch['name'])
                    # get image
                    url = "http://" + config.config['frigate']['host'] + ":" + str(config.config['frigate']['port']) + \
                        "/api/" + cameraname + "/latest.jpg"

                    req = urllib.request.urlopen(url)
                    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                    img = cv2.imdecode(arr, -1)
                    gesture = gesturemodelfunctions.gesturemodelmatch(img)
                    if len(gesture) > 0:
                        print("Gesture Recognized: " + gesture)
                    else:
                        print("No gesture recognized")

                    payload = {'person': biggestmatch['name'], 'gesture': gesture}

                    # publish results if they haven't been published already
                    if config.sentpayload[cameraname] != payload:
                        print("publishing to " + topic)
                        print("Payload: " + str(payload))
                        ret = config.client.publish(topic, json.dumps(payload), retain=True)
                        config.sentpayload[cameraname] = payload

                if nummatches == 0:
                    payload = {'person': '', 'gesture': ''}
                    if config.sentpayload[cameraname] != payload:
                        print("publishing to " + topic)
                        print("Payload: " + str(payload))
                        ret = config.client.publish(topic, json.dumps(payload), retain=True)
                        config.sentpayload[cameraname] = payload

                    print("No people recognized")

            elif numcamerapeople == 0:
                payload = {'person': '', 'gesture': ''}
                if config.sentpayload[cameraname] != payload:
                    print("publishing to " + topic)
                    print("Payload: " + str(payload))
                    ret = config.client.publish(topic, json.dumps(payload), retain=True)
                    config.sentpayload[cameraname] = payload

        time.sleep(0.5)
