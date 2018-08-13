import json
import threading

import paho.mqtt.client as mqtt
import requests

from fainting_recognition import FaintingRecognition

broker_address = 'localhost'
action_url = 'http://localhost:8000/action-service/event/'


def post(url, data):
    requests.post(url, data)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe('object-detection/objects')
    client.subscribe('object-detection/add')
    client.subscribe('object-detection/remove')


def on_message(client, userdata, msg):
    result = json.loads(msg.payload.decode())
    algorithm = algorithms[result['id']]
    event = algorithm.event(result['objects'], float(result['time']))
    if event is not None:
        print('New event detected from camera id {}'.format(result['id']))
        data = {'event': event, 'camera': result['id']}
        threading.Thread(target=post, args=(action_url, data)).start()


def on_add(client, userdata, msg):
    instance_id = msg.payload.decode()
    if algorithms.get(instance_id) is None:
        algorithms[instance_id] = FaintingRecognition()
        print('New algorithm instance created with id {}'.format(instance_id))
    else:
        print('Algorithm instance {} already exists'.format(instance_id))


def on_remove(client, userdata, msg):
    instance_id = msg.payload.decode()
    try:
        del algorithms[instance_id]
        print('Algorithm instance {} removed'.format(instance_id))
    except KeyError:
        pass


client = mqtt.Client()
client.connect(broker_address)

client.on_connect = on_connect
client.message_callback_add('object-detection/objects', on_message)
client.message_callback_add('object-detection/add', on_add)
client.message_callback_add('object-detection/remove', on_remove)

algorithms = {}

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
