#!/bin/sh

#kill existing process
sudo kill 9 $(ps -aux | grep influxdb | awk '{print $2}')

sudo kill 9 $(ps -aux | grep visualization | awk '{print $2}')

#start influxdb service
sudo nohup influxd -config /etc/influxdb/influxdb.conf & 

sleep 3s

#start the server
python server.py 