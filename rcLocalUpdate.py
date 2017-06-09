#!/usr/bin/python
#coding: utf-8
import sys
import os

def updateRCLocal():
#    os.system("/etc/rc.local < rcLocalUpdate.sh")

    os.system("sudo cat /home/pi/Documents/mochimugi/sendAllDataPicture/rcLocalUpdate.sh | > /etc/rc.local")

updateRCLocal()

