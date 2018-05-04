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

data="{"
for value_label, value in value.items():
    if value is not None:
        data +=  "'" + value_label+"':"+str(value)+","
#        data += ':'.join(value_label,value)
data += "}"

print(json.dumps(data))


# params_IM = urllib.urlencode(json.dumps(data))

