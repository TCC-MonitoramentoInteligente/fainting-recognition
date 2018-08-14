import json
import threading
import time

import paho.mqtt.client as mqtt
import requests

from fainting_recognition import FaintingRecognition

broker_address = 'localhost'
action_url = 'http://localhost:8000/actions-service/event/'


def post(url, data):
    requests.post(url, data)


def suppress_event(instance_id):
    try:
        if time.time() - event_history[instance_id] < event_suppression_time:
            print('Event from instance {} was suppressed)'.format(instance_id))
            return True
        else:
            return False
    except KeyError:
        return False


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe('object-detection/#')


def on_message(client, userdata, msg):
    result = json.loads(msg.payload.decode())
    instance_id = result['id']
    video_time = float(result['time'])
    objects = result['objects']
    try:
        algorithm = algorithms[instance_id]
    except KeyError:
        algorithms[instance_id] = algorithm = FaintingRecognition()
        print('New algorithm instance created with id {}'.format(instance_id))
    event = algorithm.event(objects, video_time)
    if event is not None and not suppress_event(instance_id):
        print("New event '{}' detected from camera id {}".format(event, instance_id))
        data = {'event': event, 'camera': instance_id}
        threading.Thread(target=post, args=(action_url, data)).start()
        event_history[instance_id] = time.time()


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
        del event_history[instance_id]
    except KeyError:
        pass


client = mqtt.Client()
client.connect(broker_address)

client.on_connect = on_connect
client.message_callback_add('object-detection/objects', on_message)
client.message_callback_add('object-detection/add', on_add)
client.message_callback_add('object-detection/remove', on_remove)

algorithms = {}
event_history = {}
event_suppression_time = 60 * 2

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
