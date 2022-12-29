#!/usr/bin/env python
from apa102_pi.driver import apa102
from time import sleep
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import json
import os
from random import randrange

class RhasspyLED(object):
  def __init__(self, rhasspy_config='/home/michael/.config/rhasspy/profiles/de/profile.json'):
    self.muted = "off"
    self.volumeOn = "100%"

    with open(rhasspy_config,'r', encoding='UTF-8') as file:
      obj = json.loads(file.read())
      MQTTconfig = json.dumps(obj["mqtt"])
      MQTTconfig = MQTTconfig.replace("\"mqtt\": ","")
      self.mqtt_config = json.loads(MQTTconfig)
      self.siteId = self.mqtt_config["site_id"]
      self.mqtt_host = self.mqtt_config["host"].strip('"')
      if "port" in json.dumps(self.mqtt_config):
        self.mqtt_port = int(self.mqtt_config["port"].strip('"'))
      else:
        self.mqtt_port = 1883

    self.strip = apa102.APA102(num_led=4)
    self.strip.clear_strip()

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
      if 'color' in payload.keys():
        color = payload['color']
      else:
        color = (randrange(0, 255), randrange(0,255), randrange(0, 255))

      for i in range(3):
        for j in range(3):
          self.strip.set_pixel(j, *color)
        self.strip.show()
        sleep(1)
        self.strip.clear_strip()
        sleep(1)

  def main(self):
    self.client = mqtt.Client()
    self.client.on_connect = self.on_connect
    self.client.on_message = self.on_message
    self.client.connect(self.mqtt_host, self.mqtt_port, 60)
    self.client.loop_start()

    BUTTON = 17

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN)
    counter = 0
    while True:
      state = GPIO.input(BUTTON)
      if state:
        counter = 0
      else:
        counter = counter + 1
        if counter == 10:
          for i in range(3):
            self.strip.set_pixel(0,255,0,0)
            self.strip.show()
            sleep(.5)
            self.strip.set_pixel(1,255,0,0)
            self.strip.show()
            sleep(.5)
            self.strip.set_pixel(2,255,0,0)
            self.strip.show()
            sleep(.5)
            self.strip.clear_strip()
            sleep(.5)
          self.strip.set_pixel(1,255,0,0)
          self.strip.show()
          os.system("shutdown -h now")
        elif counter == 3 and self.muted == "off":
          self.muted = "on"
          for i in range(0,3):
            self.strip.set_pixel(i,255,0,0)
          self.strip.show()
          os.system("amixer -q -c 'seeed2micvoicec' sset Capture 0")
        elif counter == 3 and self.muted == "on":
          self.muted = "off"
          self.strip.clear_strip()
          mixercmd = "amixer -q -c 'seeed2micvoicec' sset Capture " + self.volumeOn
          os.system(mixercmd)
        elif counter == 1:
          msg = {"modelId": "", "siteId": self.siteId}
          self.client.publish('hermes/hotword/button-press/detected', json.dumps(msg))
        sleep(.8)
      sleep(.2)

if __name__ == "__main__":
  led = RhasspyLED()
  led.main()
