import json

import paho.mqtt.client as mqtt
import time

from fainting_recognition import FaintingRecognition

client_name = 'MIA'
broker_address = 'localhost'


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe('object-detection/objects')


def on_message(client, userdata, msg):
    result = json.loads(msg.payload.decode())
    # TODO: this is not the time relative to the video
    event = algorithm.event(result.get('objects'), time.time())
    if event is not None:
        client.publish(topic='event-detection/event', payload=event)


client = mqtt.Client()
client.connect(broker_address)

client.on_connect = on_connect
client.on_message = on_message

algorithm = FaintingRecognition()

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
