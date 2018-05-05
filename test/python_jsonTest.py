#!/usr/bin/python
#coding: utf-8

import httplib, urllib

greeting="Good Day"
temperature=23.56
pressure=957
humid = None
final_greeting="Good bye!"

values={"greeting":greeting,"temperature":temperature,"pressure":pressure,"humid":humid, "final_greeting":final_greeting}

valuesToSend={}

for value_label, value in values.items():
    if value is not None:
        valuesToSend[value_label]=value

print(valuesToSend)

params_IM = urllib.urlencode(valuesToSend)

print params_IM
