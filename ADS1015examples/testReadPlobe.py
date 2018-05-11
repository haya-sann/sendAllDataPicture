#!/usr/bin/python
#coding: utf-8

from read4chAnalog import read4ch

values = [0.0]*4
read4ch(values)
print('| {0:>6,.2f} | {1:>6,.2f} | {2:>6,.2f} | {3:>6,.2f} |'.format(*values))
