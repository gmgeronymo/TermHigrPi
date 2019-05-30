# TermHigrPi

Thermohygrometer using a RaspberryPi and a DHT-22 sensor.
A chart of the temperature and humidity across time is presented in a web interface, built using CodeIgniter and ChartJS. Data is stored on a text file (accessible via a SMB share), on a sqlite3 database and optionally on an external PostgreSQL DB. 

## Install instructions

On a stock Raspian image, install the following dependencies:

```
# apt-get install pigpio python3-pigpio git samba samba-common-bin python3-psycopg2 apache2 php5 libapache2-mod-php5 sqlite3 php5-sqlite gnuplot-nox tofrodos
```

LCD

cd ~
git clone https://github.com/adafruit/Adafruit_Python_CharLCD.git
cd Adafruit_Python_CharLCD
sudo python setup.py install

Enable the pigpio service
```
# systemctl enable pigpiod
```

Enable mod_rewrite on Apache:
```
# a2enmod rewrite
```

Restart Apache: 
```
# systemctl restart apache2
```

Edit the file /etc/apache2/sites-enabled/000-default.conf and add the following lines after the line DocumentRoot /var/www/html:

```
<Directory /var/www/html>
AllowOverride All
</Directory>
```

To be able to access the log files on a SMB shared folder, we need to configure Samba.

Edit the file /etc/samba/smb.conf. Find the line workgroup and wins support, and edit like this:

```
## Browsing/Identification ###

# Change this to the workgroup/NT-domain name your Samba server will part of
   workgroup = WORKGROUP

# Windows Internet Name Serving Support Section:
# WINS Support - Tells the NMBD component of Samba to enable its WINS Server
   wins support = yes

```

On the end of the file, add the following lines:

```
[PiShare]
 comment=Logs do TermHigrPi
 path=/home/pi/
 browseable=Yes
 writeable=Yes
 only guest=no
 create mask=0777
 directory mask=0777
 public=no

```

Add the pi user to the Samba setup:

```
$ smbpasswd -a pi
```

Enable the samba service to run on boot

```
# systemctl enable smbd
```

Download TermHighPi:

```
# git clone https://github.com/gmgeronymo/TermHigrPi.git
# cd TermHigrPi/
```


Install the systemd script

```
# cp TermHigrPi.service /etc/systemd/system/
```

Enable the systemd service to run on boot

```
# systemctl enable TermHigrPi.service
```

Create a symbolic link of the html folder to the nginx root

```
# mv /var/www/html /var/www/html-bak
# ln -s /home/pi/TermHigrPi/html /var/www/html
```

The hostname can be modified on /etc/hostname.

By default, browse to http://raspberrypi to see the temperature and humidity chart.

The settings and logs can be accessed on the SMB share //raspberrypi

Reboot to complete the installation!
