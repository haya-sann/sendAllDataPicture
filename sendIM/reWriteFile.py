#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ファイルの書き換えテスト
""" 
# 
import fileinput
import os

currentDirectory = os.path.dirname(os.path.abspath(__file__))
file_name = currentDirectory + "/programmerSwitch.py"

with fileinput.FileInput(file_name, inplace=True, backup=".bak") as f:
    for line in f:
        print(line.replace("programmerSwitch = \"on\"", "programmerSwitch = \"off\""), end="")
