import json
import threading

import paho.mqtt.client as mqtt
import requests

from fainting_recognition import FaintingRecognition

client_name = 'MIA'
broker_address = 'localhost'
action_url = 'http://localhost:8000/action-service/event/'


def post(url, data):
    requests.post(url, data)


def get_algorithm(camera_id):
    for algorithm in algorithm_list:
        if algorithm['id'] == camera_id:
            return algorithm['algorithm']
    algorithm = {'id': camera_id, 'algorithm': FaintingRecognition()}
    print('New algorithm instance created to camera id {}'.format(camera_id))
    return algorithm['algorithm']


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe('object-detection/objects')


def on_message(client, userdata, msg):
    result = json.loads(msg.payload.decode())
    algorithm = get_algorithm(result['id'])
    event = algorithm.event(result['objects'], float(result['time']))
    if event is not None:
        print('New event detected from camera id {}'.format(result['id']))
        data = {'event': event, 'camera': result['id']}
        threading.Thread(target=post, args=(action_url, data)).start()


client = mqtt.Client()
client.connect(broker_address)

client.on_connect = on_connect
client.on_message = on_message

algorithm_list = []

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
