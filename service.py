import json
import threading
import time

import paho.mqtt.client as mqtt
import requests

from fainting_recognition import FaintingRecognition

BROKER_IP = '10.1.0.2'
ACTIONS_SERVICE_IP, ACTIONS_SERVICE_PORT = '10.1.0.5', 8050

action_url = 'http://{}:{}/actions-service/event/'\
    .format(ACTIONS_SERVICE_IP, ACTIONS_SERVICE_PORT)


def post(url, data):
    error = 'Action error. Event from camera {} could not ' \
            'be notified to actions service'.format(data['camera'])
    try:
        action_request = requests.get(url, data, timeout=3)
        if action_request.status_code != requests.codes.ok:
            client.publish(topic='fainting-recognition/logs/error', payload=error)
    except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError):
        client.publish(topic='fainting-recognition/logs/error', payload=error)


def suppress_event(instance_id):
    try:
        if time.time() - event_history[instance_id] < event_suppression_time:
            print('Event from instance {} was suppressed'.format(instance_id))
            client.publish(topic='fainting-recognition/logs/success',
                           payload='[event suppression] Event from instance {} was suppressed'.format(instance_id))
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
    instance_id = result['cam_id']
    video_time = float(result['time'])
    objects = result['objects']
    try:
        algorithm = algorithms[instance_id]
    except KeyError:
        algorithms[instance_id] = algorithm = FaintingRecognition()
        print('New algorithm instance created with id {}'.format(instance_id))
        client.publish(topic='fainting-recognition/logs/success',
                       payload='[algorithm instance] New algorithm instance created with id {}'.format(instance_id))
    event = algorithm.event(objects, video_time)
    if event is not None and not suppress_event(instance_id):
        print("New event '{}' detected from camera id {}".format(event, instance_id))
        client.publish(topic='fainting-recognition/logs/success',
                       payload="[event detected] Event '{}' detected from camera id {}".format(event, instance_id))
        data = {'event': event, 'cam_id': instance_id}
        threading.Thread(target=post, args=(action_url, data)).start()
        event_history[instance_id] = time.time()


def on_add(client, userdata, msg):
    instance_id = msg.payload.decode()
    if algorithms.get(instance_id) is None:
        algorithms[instance_id] = FaintingRecognition()
        print('New algorithm instance created with id {}'.format(instance_id))
        client.publish(topic='fainting-recognition/logs/success',
                       payload='[algorithm instance] New algorithm instance created with id {}'.format(instance_id))
    else:
        print('Algorithm instance {} already exists'.format(instance_id))


def on_remove(client, userdata, msg):
    instance_id = msg.payload.decode()
    try:
        del algorithms[instance_id]
        print('Algorithm instance {} removed'.format(instance_id))
        client.publish(topic='fainting-recognition/logs/success',
                       payload='[algorithm instance] Algorithm instance {} removed'.format(instance_id))
        del event_history[instance_id]
    except KeyError:
        pass


client = mqtt.Client()
try:
    client.connect(BROKER_IP)
except (OSError, ConnectionRefusedError):
    print('Could not connect to broker. Check if it is running and try again.')
    exit(0)

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
