#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
"""
Gmail
Gmailで簡単にメール送信
"""
 
import os.path
import datetime
import smtplib
from email import Encoders
from email.Utils import formatdate
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
 
#Gmailアカウント
"""
ADDRESS = "haya.biz@gmail.com"
PASSWARD = "eiinxgvsmspnwkks"
"""
ADDRESS = "iPhone.Concier@gmail.com"
PASSWARD = "vtaolksmyqfxcqbw"

 
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
 
def send(from_addr, to_addrs, msg):
    """
    メールを送信する
    @:param from_addr 差出人
    @:param to_addr 宛先(list)
    @:param msg メッセージ
    """
    smtpobj = smtplib.SMTP(SMTP, PORT)
    smtpobj.ehlo()
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(ADDRESS, PASSWARD)
    smtpobj.sendmail(from_addr, to_addrs, msg.as_string())
    smtpobj.close()
 
 
if __name__ == '__main__':
 
    #宛先アドレス
    to_addr = "haya.biz@gmail.com"
 
    #件名と本文
    subject = "件名:Pythonでメールを送る件"
    body = """本文:
    （トリプルクォートを使って複数行の文章を書けばよい）
    
    ここは4行目？
    今度は5行目。
    (改行を3行入れる)



    （空行が3行はいりました）
    以上です。さようなら
    """
 
    #添付ファイル設定(text.txtファイルを添付)
    mime={'type':'text', 'subtype':'comma-separated-values'}
    attach_file={'name':'test.txt', 'path':'/home/pi/nas/test/testMail/test.txt'}
 
    #メッセージの作成(添付ファイルあり)
    msg = create_message(ADDRESS, to_addr, subject, body, mime, attach_file)
 
    #メッセージ作成(添付ファイルなし)
    #msg = create_message(ADDRESS, to_addr, subject, body)
 
    #送信
    send(ADDRESS, [to_addr], msg)


