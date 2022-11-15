import threading
import mqtthandlers
import config
import gesturedetection

config.init()

config.client.on_connect = mqtthandlers.on_connect
config.client.on_message = mqtthandlers.on_message
config.client.on_publish = mqtthandlers.on_publish

config.client.connect(config.config['mqtt']['host'], config.config['mqtt']['port'], 60)

t1 = threading.Thread(target=gesturedetection.lookforhands)
t1.start()

config.client.loop_forever()
