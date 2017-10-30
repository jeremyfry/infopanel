"""MQTT client to get data into the display from some data source."""

import logging

import paho.mqtt.client as mqtt
import json

LOG = logging.getLogger(__name__)

class MQTTClient(object):
    """MQTT Client."""

    def __init__(self, data_container, conf):
        self._client = None
        self._data_container = data_container
        self.conf = conf

    def on_connect(self, client, userdata, flags, rc):  # pylint: disable=unused-argument, invalid-name
        """Callback for when MQTT server connects."""
        LOG.info("Connected with result code %d", rc)
        client.subscribe(self.conf['topic'])  # subscribe in case we get disconnected

    def on_message(self, client, userdata, msg):  # pylint: disable=unused-argument
        """Callback for when MQTT receives a message."""
        LOG.debug("%s %s", msg.topic, str(msg.payload))
        key = msg.topic.split('/')[-1]
        if key == 'multi':
            try:
                values = json.loads(msg.payload)
                for valueKey, value in values.iteritems():
                    self._data_container[valueKey] = value
            except ValueError, e:
                LOG.debug("Bad JSON", e)
        else:
            self._data_container[key] = msg.payload

    def start(self):
        """Connect to the MQTT server."""
        conf = self.conf
        LOG.info('Connecting to MQTT server at %s', conf['broker'])
        self._client = mqtt.Client(conf['client_id'], protocol=conf['protocol'])
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        if conf.get('username'):
            self._client.username_pw_set(conf['username'], conf['password'])
        if conf.get('certificate'):
            self._client.tls_set(conf['certificate'])
        self._client.connect(conf['broker'], conf['port'], conf['keepalive'])
        self._client.loop_start()

    def stop(self):
        """End the MQTT connection."""
        self._client.loop_stop()
