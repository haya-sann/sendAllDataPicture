#!/usr/bin/python
#coding: utf-8
import sys
import os

def updateRCLocal():
#    os.system("/etc/rc.local < rcLocalUpdate.sh")

    os.system("sudo cp /home/pi/Documents/field_location/sendAllDataPicture/rcLocalUpdate.sh /etc/rc.local")

updateRCLocal()

