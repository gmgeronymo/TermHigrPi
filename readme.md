# TermHigrPi

Thermohygrometer using a RaspberryPi and a DHT-22 or BME-280 sensor.
A chart of the temperature and humidity across time is presented in a web interface, built using Flask and ChartJS. Data is stored on a text file, on a sqlite3 local database and optionally on an external server via a REST API. 

## Install instructions

On a stock Raspian image, install the following dependencies:

```
# apt install pigpio python3-pigpio python3-sqlite3 python3-flask git 
```

Enable the pigpio service
```
# systemctl enable pigpiod
```

Download TermHighPi:

```
# git clone https://github.com/gmgeronymo/TermHigrPi.git
# cd TermHigrPi/
```

Install the systemd script

```
# cp TermHigrPi.service /etc/systemd/system/
# cp dashboard.service /etc/systemd/system/
```

Enable the systemd service to run on boot

```
# systemctl enable TermHigrPi.service
# systemctl enable dashboard.service
```

The hostname can be modified on /etc/hostname.

By default, browse to http://raspberrypi:8080 to see the temperature and humidity chart.

Reboot to complete the installation!
