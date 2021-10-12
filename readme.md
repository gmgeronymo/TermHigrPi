# TermHigrPi

Thermohygrometer using a RaspberryPi and a DHT-22 or BME-280 sensor.
A chart of the temperature and humidity across time is presented in a web interface, built using Flask and ChartJS. Data is stored on a text file, on a sqlite3 local database and optionally on an external server via a REST API. 

## Install instructions

On a stock Raspian image, install the following dependencies:

```
# apt install python3-flask python3-pandas git 
```

For sensors DHT22 and BME280, install pigpio:

```
# apt install pigpio python3-pigpio 
```

For Rotronic Hygropalm 2 or Sato SK-L200TH, install pyserial:

```
# apt install python3-serial 
```

To use calibration certificate corrections, install numpy:

```
# apt install python3-numpy 
```

If you plan to use DHT22 or BM280, enable the pigpio service:
```
# systemctl enable pigpiod
# systemctl start pigpiod
```

Download TermHighPi:

```
$ git clone https://github.com/gmgeronymo/TermHigrPi.git
# cd TermHigrPi/
```

Install the systemd script

```
# cp *.service /etc/systemd/system/
```

Copy the configuration files to /boot :

```
# cp config/*.ini /boot/
```

Adjust the settings in /boot/datalogger.ini. If you plan to use calibration certificate corrections, put the information in /boot/cal.ini.

Enable the systemd service to run on boot

```
# systemctl enable TermHigrPi.service
# systemctl enable dashboard.service
# systemctl start TermHigrPi.service
# systemctl start dashboard.service
```

The hostname can be modified on /etc/hostname.

By default, browse to http://raspberrypi:8080 to see the temperature and humidity chart.

