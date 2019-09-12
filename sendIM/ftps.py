#!/usr/bin/python
#coding: utf-8

import datetime # datetimeモジュールのインポート
import os

import configparser
from ftplib import FTP_TLS
PYTHONIOENCODING = 'utf_8'
configfile = configparser.SafeConfigParser() #sftpサーバーへの接続準備
configfile.read("/home/pi/Documents/field_location/config.conf")#Localに置いたconfig.confファイルへの絶対パスを使った

host_IM = configfile.get("settings", "host")
archive_server = configfile.get("settings", "ftpsHost")  #ftpsサーバーのドメイン名
pw = configfile.get("settings", "password")      #ログインパスワード
userID = configfile.get("settings", "id")        #サーバーログインUser id

from __init__ import get_module_logger #log保存先は/var/log/field_location.log
logger = get_module_logger(__name__)

logger.propagate = True

def sendLog_ftps(file_name, put_directory):
    try:
        logger.info("BOM_UTF8対応対策済みftps.py:2018/06/20")
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(0) # デバッグログを全部出力してみよう
    #    _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
        _ftps.login(userID, pw)
        _ftps.prot_p() #データ接続をセキュアにするには、
        #ユーザが prot_p() メソッドを呼び出してそれを明示的に要求しなければなりません。

        _file = open('/var/log/' + file_name, 'rb') #'r' means read as text mode
        #'rb' means binarymode
        _timeStamp = datetime.datetime.now()
        file_name = os.path.basename(file_name)#get fileName
        logfile_name = _timeStamp.strftime('%Y%m%d%H%M') + file_name + '.txt' #changed name space

        _ftps.cwd('seasonShots/' + put_directory) #アップロード先ディレクトリに移動

    #        _ftps.storlines('STOR ' + logfile_name, _file)
        _ftps.storbinary('STOR ' + logfile_name, _file)

        logger.info("Upload finished:" + put_directory + "/" +logfile_name +  " from " + file_name + " with no error. Will clear log file.")

        _file.close()
    #        _ftps.quit() ##変なエラーが起きるので、これをコメントアウト
        return _timeStamp

    except Exception as e:
        logger.debug("send(picture)_ftps error. :" + str(e))
        _file.close()
        _ftps.quit()
        pass


def send_ftps(file_name, put_directory): #エラー処理 will be raise to main()
    try:
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(0) # デバッグログを取らない
#        _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
        _ftps.login(userID, pw)
        _ftps.prot_p() #データ接続をセキュアにする

        _file = open(file_name, 'rb') #'rb'means read as binary mode.
        # アップロードが成功したらファイルは削除。2017/06/23

        _ftps.cwd('/seasonShots/' + put_directory) #アップロード先ディレクトリに移動.ロリポップの場合、webルートに入ってくる
        _ftps.storbinary('STOR ' + file_name, _file)
        _file.close()
        _ftps.quit()
        logger.info("Upload finished with no error to: /seasonShots/" + put_directory + "/" + file_name)

    except Exception as e:
        logger.debug("send(picture)_ftps error. :" + str(e))
        _file.close()
        _ftps.quit()
        pass


