#!/usr/bin/env python
# coding:UTF-8

class Prism:
    def __init__(self, width, height, depth):
        self.width = width      # ここでクラスのメンバーが定義されているのに注意
        self.height = height
        self.depth = depth

    def content(self):
        return self.width * self.height * self.depth

        