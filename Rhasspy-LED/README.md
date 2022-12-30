
# Rhasspy-LED
LED-Service for Rhasspy on Raspberry Zero 2W and ReSpeaker 2-mic hat

On wakeword detection, the LEDs turn green, after your voice command they turn blue until the ond of the session.
A single button press starts a new session.
Holding the button for at least 3s disables hotword detection on this satellite. The LEDs turn solid red.
Holding hte button for at least 10s safely shuts down the Pi.


## Install Driver  
``` bash
sudo apt-get update 
sudo apt-get upgrade 
git clone https://github.com/respeaker/seeed-voicecard.git 
cd seeed-voicecard 
sudo ./install.sh 
sudo reboot
```

## Install Service  
Use 'raspi-config' to enable SPI.
``` bash
sudo git clone https://github.com/michaeldaas/rhasspy-led.git 
sudo pip3 install rpi.gpio apa102_pi 
sudo apt-get install python3-paho-mqtt
```

Edit correct path in rhasspy-led.service according to your installation

``` bash
sudo cp ./rhasspy-led/Rhasspy-LED/rhasspy-led.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rhasspy-led.service
```
