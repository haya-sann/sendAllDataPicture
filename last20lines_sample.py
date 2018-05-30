#!/usr/bin/python
#coding: utf-8

# IMに全データ＋logの最終20行分を送信
put_directory = 'daily_timelapseSandbox' 
dir_path = '/home/pi/Documents/field_location/'+ put_directory

import logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter('[%(name)s] %(asctime)s : %(message)s')
streamHandler = logging.StreamHandler()

fileHandler = logging.FileHandler(dir_path + '/'+ 'test.log', mode='a', encoding=None, delay=0)
fileHandler.setFormatter(formatter)
streamHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
streamHandler.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.debug("dir_path is set to : " + dir_path + "(just for debugging)")



logger.debug(dir_path + '/'+ 'field_location.logからこれまでのログを読込む')
total_lines = sum(1 for line in open(dir_path + '/'+ 'field_location.log'))
logger.debug("Total lines : " + str(total_lines))

fileObject = open(dir_path + '/'+ 'field_location.log', 'r')
logger.debug('Opened log file')
readBuffer = fileObject.readlines()
last20linesLog = '## Last 20 lines from field_location.log ##' + '\n'#init string
if total_lines-20 < 0:
    startLine = 0
startLine = total_lines-20

for num_lines in range(startLine, total_lines):
    last20linesLog = last20linesLog + readBuffer[num_lines]

logger.debug(last20linesLog + "this is debugging only")

fileObject.close
logger.debug('File is closed safely')
