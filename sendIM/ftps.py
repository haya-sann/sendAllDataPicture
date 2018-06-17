#!/usr/bin/python
#coding: utf_8

import datetime # datetimeモジュールのインポート
import codecs

import ConfigParser
from ftplib import FTP_TLS
PYTHONIOENCODING = 'utf_8'
configfile = ConfigParser.SafeConfigParser() #sftpサーバーへの接続準備
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
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(1) # デバッグログを全部出力してみよう
    #    _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
        _ftps.login(userID, pw)
        _ftps.prot_p() #データ接続をセキュアにするには、
        #ユーザが prot_p() メソッドを呼び出してそれを明示的に要求しなければなりません。

        _file = open('/var/log/' + file_name, 'rb') #'r' means read as text mode
        #'rb' means binarymode
        _timeStamp = datetime.datetime.now()
        logfile_name = 'field_location' + _timeStamp.strftime('%Y%m%d%H%M') + '.log'

        _ftps.cwd('seasonShots/' + put_directory) #アップロード先ディレクトリに移動

        logger.info("Upload finished:" + put_directory + "/" +logfile_name + " with no error. Will clear log file.")

#        _ftps.storlines('STOR ' + logfile_name, _file)
        _ftps.storbinary('STOR ' + logfile_name, _file)

        _file.close()
#        _ftps.quit() ##変なエラーが起きるので、これをコメントアウト
        #log送信正常終了なので、中身をクリアする
        with codecs.open('/var/log/' + file_name, 'w', 'utf_8') as f:
            f.write(codecs.BOM_UTF8.encode('utf_8'))
            f.write (u'アップロード終了 with no error. Log cleared at: ' + _timeStamp.strftime('%Y%m%d%H%M') + '\n'.encode('utf_8'))
#            f.write(unicode ((u'アップロード終了 with no error. Log cleared at: ' + _timeStamp.strftime(u'%Y%m%d%H%M') + u'\n').encode('utf_8','ignore'),'utf_8'))
#            f.close() #with openの場合、これは不要らしい。
        return logfile_name
    except Exception as e:
        logger.debug("sendLog_ftps error. :" + str(e))
        _file.close()
        _ftps.quit()
        raise

def send_ftps(file_name, put_directory): #エラー処理 will be raise to main()
    try:
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
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
        raise

