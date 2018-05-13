#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
"""
Gmail
Gmailで簡単にメール送信
"""

import os 
import time
import os.path
import datetime
import smtplib
import commands
import ConfigParser
from email import Encoders
from email.Utils import formatdate
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

#from retry import retry

from __init__ import get_module_logger
logger = get_module_logger(__name__)

logger.propagate = True

#メールアカウント情報取得
configfile = ConfigParser.SafeConfigParser() #sftpサーバーへの接続準備
configfile.read("../../kawagoe_config.conf")
from_addr = configfile.get("settings", "mailAddress")
mailPass = configfile.get("settings", "mailPass")

from_addr = from_addr
mailPass = mailPass

now = datetime.datetime.now() #ntp からのデータをアップデート
os.system('ntpq -p')
 
#SMTPサーバの設定(Gmail用)
SMTP = "smtp.gmail.com"
PORT = 587
 
def create_message(from_addr, to_addr, subject, body, mime=None, attach_file=None):
    """
    メッセージを作成する
    @:param from_addr 差出人
    @:param to_addr 宛先
    @:param subject 件名
    @:param body 本文
    @:param mime MIME
    @:param attach_file 添付ファイル
    @:return メッセージ
    """
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Date"] = formatdate()
    msg["Subject"] = subject
    body = MIMEText(body)
    msg.attach(body)
 
    # 添付ファイル
    if mime != None and attach_file != None:
        attachment = MIMEBase(mime['type'],mime['subtype'])
        file = open(attach_file['path'])
        attachment.set_payload(file.read())
        file.close()
        Encoders.encode_base64(attachment)
        msg.attach(attachment)
        attachment.add_header("Content-Disposition","attachment", filename=attach_file['name'])
 
    return msg
 
def send(from_addr, to_addr, msg):
    """
    メールを送信する
    @:param from_addr 差出人
    @:param to_addr 宛先(list)
    @:param msg メッセージ
    """
    print(from_addr,to_addr)

    smtpobj = smtplib.SMTP(SMTP, PORT)
    smtpobj.ehlo()
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(from_addr, mailPass)
    smtpobj.sendmail(from_addr, to_addr, msg.as_string())
    smtpobj.close()


if __name__ == '__main__':
    now = datetime.datetime.now()
    hour = now.hour
    min = now.minute
    sec = now.second
    print(now)
    print(hour)
    print(min)
    print(sec)
    #宛先アドレス
    to_addr = "haya.biz@gmail.com"
 
    #件名と本文
    subject = str(hour) + ":" + str(min) + ":" + str(sec)
    ntpStatus = commands.getoutput('ntpq -p')
    powerControlCommand = '/usr/sbin/i2cset -y 1 0x40 40 1 i'
    body = """本文:
    電源モジュールが動作しました
    """ + ntpStatus + "\n\nパワーコントロールモジュールに" + powerControlCommand + "を送信しました" + "\n"

 
    #添付ファイル設定(text.txtファイルを添付)
    mime={'type':'text', 'subtype':'comma-separated-values'}
#    attach_file={'name':'boot.log', 'path':'/var/log/wifi.log'}
    attach_file={'name':'boot.log', 'path':'/var/log/boot.log'}
 
    #メッセージの作成(添付ファイルあり)
    msg = create_message(from_addr, to_addr, subject, body, mime, attach_file)
 
    #メッセージ作成(添付ファイルなし)
    #msg = create_message(ADDRESS, to_addr, subject, body)
 
    #送信
    send(from_addr, to_addr, msg)
    time.sleep(5) #import timeが必要


