import config


def on_publish(client,userdata,result):
    pass


def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

    # get the name of the camera
    list = msg.topic.split("/")
    msgcam = list[1]

    # update the numpersons dictionary
    try:
        config.numpersons[msgcam] = int(msg.payload)
    except:
        config.numpersons[msgcam] = 0


# set up subscriptions when connecting completes.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    for camera in config.config['frigate']['cameras']:
        client.subscribe("frigate/" + camera + "/person")

