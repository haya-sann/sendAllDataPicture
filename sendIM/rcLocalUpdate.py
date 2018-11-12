#!/usr/bin/python
#coding: utf-8
#import sys
import os

def updateRCLocal():

    os.system("sudo cp -vu /home/pi/Documents/field_location/sendAllDataPicture/rcLocalUpdate.sh /etc/rc.local")

updateRCLocal()

