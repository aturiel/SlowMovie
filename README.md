# SlowMovie Server

![](Extras/IMG_5770.jpg)
![](Extras/IMG_5768.jpg)


## Based on  
Python / Raspberry Pi interpretation of Bryan Boyer's Very Slow Movie Player:   
https://medium.com/@tomwhitwell/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4

Bryan's original post here:  
https://medium.com/s/story/very-slow-movie-player-499f76c48b62  

## Homepage
Integrated homepage will allow yo to change playyer settings
 - random frame
 - frames skipped
 - delay between frames
 - current movie and frame
 - manage favorite frames: to directly display selected frames from your movies

Build with [Materialize CSS](https://materializecss.com">)

![](Extras/homepage.jpg)

## Run Slow Movie Server
```Shell
cd /home/pi/SlowMovie

pip3 install -U Jinja2

python3 smserver.py
```

## Run a Script as a Service in Raspberry Pi
To define the service to run this script
```Shell
cd /lib/systemd/system/
sudo nano slowmovie.service
```
The service definition must be on the /lib/systemd/system folder. Our service is going to be called "slowmovie.service":
```text
[Unit]
Description=Slow Movie
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/bin/python3 smserver.py
WorkingDirectory=/home/pi/SlowMovie
Restart=on-abort

[Install]
WantedBy=multi-user.target
```
Now we need to activate oir service:
```Shell
sudo systemctl daemon-reload
sudo systemctl enable slowmovie.service
sudo systemctl start slowmovie.service
````

## Service Tasks
For every change that we do on the /lib/systemd/system folder we need to execute a daemon-reload (first line of previous code). If we want to check the status of our service, you can execute:

`sudo systemctl status slowmovie.service`

In general:

### Check status
`sudo systemctl status slowmovie.service`

### Start service
`sudo systemctl start slowmovie.service`

### Stop service
`sudo systemctl stop slowmovie.service`

### Restart (stop & start) service
`sudo systemctl restart slowmovie.service`

### Check service's log
`sudo journalctl -f -u slowmovie.service`

## 3D Printer parts
[Raspberry Pi 3B+ case](https://www.thingiverse.com/thing:3361218) based on a design from [mkellsy](https://www.thingiverse.com/mkellsy). Frame is an [IKEA RIBBA](https://www.ikea.com/es/es/p/ribba-marco-negro-50378448/) 13x18cm.

- Frame adjustment - https://www.tinkercad.com/things/8cEJlHhdwC7
- Frame back panel - https://www.tinkercad.com/things/24gwuQ8l2YA
- PI back & frame support - https://www.tinkercad.com/things/72tjLu8RRyo

## REFERENCES
- https://www.raspberrypi.org/documentation/linux/usage/systemd.md
- https://gist.github.com/emxsys/a507f3cad928e66f6410e7ac28e2990f
- https://wiki.archlinux.org/index.php/systemd
- https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files
- https://www.tutorialdocs.com/article/getting-started-with-systemd-in-practice.html
- https://materializecss.com



