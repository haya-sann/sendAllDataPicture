#!/usr/bin/python
#coding: utf-8

import httplib, urllib
import json

greeting="Good Day"
temperature=23.56
pressure=957
humid = None
final_greeting="Good bye!"

value={"greeting":greeting,"temperature":temperature,"pressure":pressure,"humid":humid,"final_greeting":final_greeting}

urlValue="{"
for value_label, value in value.items():
    if value is not None:
        urlValue +=  "'" + value_label+"':'"+str(value)+"',"
#        data += ':'.join(value_label,value)
urlValue += "}"
print urlValue
print(json.dumps(urlValue))
params_IM = urllib.urlencode({'pressure':'957','greeting':'Good Day','final_greeting':'Good bye!','temperature':'23.56'})
print params_IM
#params_IM = urllib.urlencode(urlValue)

# params_IM = urllib.urlencode(json.dumps(data))

