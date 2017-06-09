#!/usr/bin/python
#coding: utf-8
import sys
import os

def updateRCLocal():
#    os.system("/etc/rc.local < rcLocalUpdate.sh")

    os.system("/etc/rc.local < /home/pi/Documents/mochimugi/sendAllDataPicture/rcLocalUpdate.sh")

updateRCLocal()

