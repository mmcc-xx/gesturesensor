# gesturesensor

This app works with [Frigate](https://frigate.video/) and [Double-Take](https://github.com/jakowenko/double-take) to detect if...
1. There's a recognized person standing in front of your camera, and
2. There is a recognized hand gesture on display

If only condition 1 is met, an MQTT message is published indicating the name of the person detected. If both conditions 
are detected, the name of the gesture is also published.

The topic published to is from the config file plus the name of the camera, e.g.:

    gestures/<cameraname>

The payload of the publications is JSON in this format:

    {'person': '<name from double-take>', 'gesture': '<gesture name from gesture model>'}

When there are no recognized people, an empty name and gesture are published:

    {'person': '', 'gesture': ''}

## How It Works

Gesture recognition is done by first detecting hands and hand positions using [MediaPipe](https://google.github.io/mediapipe/). The hand position data is then
fed into a neural net model to determine the gesture.

I swiped the model and some code for using the model from
https://github.com/kinivi/tello-gesture-control as I really didn't want to train my own model and copying code is easier
than writing code. As such the gestures are oriented to controlling a drone. But, why shouldn't I Land my garage door?

Take a look at [supportedgestures.jpg](./supportedgestures.jpg) to see the supported gestures.

## Requirements

To make this work, you'll need...
- An MQTT broker. Authentication not currently supported
- Frigate installed and working, publishing events to the MQTT broker on topic "frigate"
- Double-Take installed and working. This does not need to be doing anything on MQTT - its REST API is used
- Python - I'm using 3.8, and the Docker file is set to use 3.8

If you aren't using Docker, check the requirements.txt file for the libraries that you need. 

## Configuration

Configuration is via config.yml. This file is expected to be at /config/config.yml. Here you can set...
- The address of your mqtt broker
    - Note that authentication for the mqtt broker is not currently supported
- The address of your frigate server and cameras to be monitored
    - Note that the app listens for mqtt publications from your frigate server and the topic is assumed to be "frigate"
- The address of your double-take server
- Some configuration for gesture recognition, including
    - The box size in a camera image necessary for a hand to be considered a hand
    - The confidence level necessary for a gesture to be considered a gesture
    - The topic to publish to

## Running as a Docker Container

You can build this app into a docker container with the included Dockerfile and this command:

    docker build -t gesturesensor .

If you are inclined to use docker-compose you can use the included docker-compose.yml file as a starting point. It will 
allow you to point at the location of your config file.

If you use docker run, you'll need to set up a volume to point your config file at /config/config.yml

## Home Assistant Integration

For my garage camera, I have integrated this with Home Assistant using an mqtt sensor. I configured this sensor in 
configuration.yaml like so:

    mqtt:
      sensor:
        - name: "Garage Gesture"
          unique_id: garage_gestures
          state_topic: "gestures/garage"
          availability:
            - topic: "gestures/availability"
          value_template: "{{ value_json.gesture }}"
          json_attributes_topic: "gestures/garage"
          json_attributes_template: "{{ value }}" tojson }}"

This gives you a sensor with a value of the current gesture, and attributes of the current person and the current
gesture. I then set up an automation that reacts to either of the attributes changing, and takes action if the current
person and gesture match specific values.