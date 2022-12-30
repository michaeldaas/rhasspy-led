#!/usr/bin/env python
from apa102_pi.driver import apa102
from time import sleep
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import json
import os
from random import randrange

class RhasspyLED(object):
  def __init__(self, rhasspy_config='/home/pi/.config/rhasspy/profiles/en/profile.json'):
    self.muted = False

    with open(rhasspy_config,'r', encoding='UTF-8') as file:
      obj = json.loads(file.read())
      MQTTconfig = json.dumps(obj["mqtt"])
      MQTTconfig = MQTTconfig.replace("\"mqtt\": ","")
      mqtt_config = json.loads(MQTTconfig)
      self.siteId = mqtt_config["site_id"]
      mqtt_host = mqtt_config["host"].strip('"')
      if "port" in json.dumps(mqtt_config):
        mqtt_port = int(mqtt_config["port"].strip('"'))
      else:
        mqtt_port = 1883

    self.strip = apa102.APA102(num_led=4)
    self.strip.clear_strip()

    self.client = mqtt.Client()
    self.client.on_connect = self.on_connect
    self.client.on_message = self.on_message
    self.client.connect(mqtt_host, mqtt_port, 60)
    self.client.loop_start()

    self._hello()

  def _hello(self, speed=1):
    self.strip.set_pixel(0, 255,0,0)
    self.strip.show()
    sleep(speed)
    self.strip.set_pixel(0, 255,255,0)
    self.strip.set_pixel(1, 255,255,0)
    self.strip.show()
    sleep(speed)
    self.strip.set_pixel(0, 0,255,0)
    self.strip.set_pixel(1, 0,255,0)
    self.strip.set_pixel(2, 0,255,0)
    self.strip.show()
    sleep(speed * 3)
    self.strip.clear_strip()

  def _count_up(self, color, speed=.3):
      self.strip.set_pixel(0, *color)
      self.strip.show()
      sleep(speed)
      self.strip.set_pixel(1, *color)
      self.strip.show()
      sleep(speed)
      self.strip.set_pixel(2, *color)
      self.strip.show()
      sleep(speed)

  def _count_down(self, color, speed=.3):
      self.strip.set_pixel(0, *color)
      self.strip.set_pixel(1, *color)
      self.strip.set_pixel(2, *color)
      self.strip.show()
      sleep(speed)
      self.strip.set_pixel(0, 0,0,0)
      self.strip.show()
      sleep(speed)
      self.strip.set_pixel(1, 0,0,0)
      self.strip.show()
      sleep(speed)
      self.strip.clear_strip()

  def _blink(self, color, times, speed=.3):
    for j in range(times):
      self.strip.set_pixel(0, *color)
      self.strip.set_pixel(1, *color)
      self.strip.set_pixel(2, *color)
      self.strip.show()
      sleep(speed)
      self.strip.clear_strip()
      sleep(speed)

  def on_connect(self, client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("hermes/hotword/+/detected")
    client.subscribe("hermes/asr/stopListening")
    client.subscribe("hermes/nlu/intentNotRecognized")
    client.subscribe("hermes/dialogueManager/sessionEnded")
    client.subscribe("home/rhasspy/blink")

  def on_message(self, client, userdata, msg):
    payload = json.loads(msg.payload)
    if 'sessionId' in payload.keys():
      this_session = payload['sessionId'] #TODO check session id with stopListening, sessionEnded and intentNotRecognized events

    if 'hermes/hotword' in msg.topic and 'detected' in msg.topic and payload["siteId"] == self.siteId:
      for i in range(0,3):
        self.strip.set_pixel(i,0,255,0)
      self.strip.show()
    elif msg.topic == "hermes/asr/stopListening" and payload['siteId'] == self.siteId:
      for i in range(0,3):
        self.strip.set_pixel(i,0,0,255)
      self.strip.show()
    elif msg.topic == "hermes/dialogueManager/sessionEnded" and payload['siteId'] == self.siteId:
      self.strip.clear_strip()
    elif msg.topic == "hermes/nlu/intentNotRecognized" and payload['siteId'] == self.siteId:
      for i in range(0,3):
        self.strip.set_pixel(i,255,0,0)
      self.strip.show()
      sleep(3)
      self.strip.clear_strip()
    elif msg.topic == "home/rhasspy/blink" and self.siteId in payload['siteId']:
      color = payload['color'] if 'color' in payload.keys() else (randrange(0, 255), randrange(0,255), randrange(0, 255))
      times = payload['times'] if 'times' in payload.keys() else 3
      speed = payload['speed'] if 'speed' in payload.keys() else .5

      self._blink(color, times, speed)

  def button_loop(self):
    BUTTON = 17

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN)
    counter = 0
    while True:
      sleep(.2)
      state = not GPIO.input(BUTTON)
      if not state:
        if counter > 0:
          self._button_pressed(counter)
        counter = 0
        continue
      else:
        counter += 1

        if counter == 50:
          self._blink((255,0,0), 3, .1)
        elif counter == 15:
          self._blink((255,0,0), 1, .1)

  def _button_pressed(self, counter):
    if counter >= 50:
      self._count_down((255,0,0), 1)
      os.system("shutdown -h now")
    elif counter >= 15 and not self.muted:
      self.muted = True
      for i in range(0,3):
        self.strip.set_pixel(i,255,0,0)
      self.strip.show()
      msg = {'siteId': self.siteId, 'customData':{'reason': 'muted'}}
      self.client.publish('hermes/hotword/toggleOff', json.dumps(msg))
    elif counter >= 15 and self.muted:
      self.muted = False
      self.strip.clear_strip()
      msg = {'siteId': self.siteId, 'customData':{'reason': 'unmuted'}}
      self.client.publish('hermes/hotword/toggleOn', json.dumps(msg))
    elif counter >= 1:
      msg = {"modelId": "", "siteId": self.siteId}
      self.client.publish('hermes/hotword/button-press/detected', json.dumps(msg))


if __name__ == "__main__":
  led = RhasspyLED(rhasspy_config='/home/michael/.config/rhasspy/profiles/de/profile.json')
  led.button_loop()
