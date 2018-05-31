#!/usr/bin/python
#coding: utf-8

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
        logger.info("Sending log with ftps to server : "+ archive_server)
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(1) # デバッグログを全部出力してみよう
    #    _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
        _ftps.login(userID, pw)
        _ftps.prot_p() #データ接続をセキュアにするには、
        #ユーザが prot_p() メソッドを呼び出してそれを明示的に要求しなければなりません。

        _file = open('/var/log/' + file_name, 'rb') #'r' means read as text mode
        #'rb' means binarymode
        logger.info("File opened : " + '/var/log/' + file_name)
        _timeStamp = datetime.datetime.now()
        logfile_name = 'field_location' + _timeStamp.strftime('%Y%m%d%H%M') + '.log'
        logger.info('Logging file on the server is : ' + logfile_name)

        _ftps.cwd('/seasonShots/' + put_directory) #アップロード先ディレクトリに移動
        logger.info('Success : Change directory to: /home/field_location/www/seasonShots/' + put_directory)

        _ftps.storbinary('STOR ' + logfile_name, _file)

        # process = Popen(ftps_storeCommand, shell=True, stdout=PIPE, stderr=PIPE)
        # output, err = process.communicate()

        # for line in _file:
        #     print line
        
        _file.close()
        _ftps.quit()
        logger.info("Upload finished and closed Log file, with no error. Clear log file.")
        #log送信正常終了なので、中身をクリアする
        with open(dir_path + '/' + file_name, "w") as f:
            f.write("Log cleared at: " + _timeStamp.strftime('%Y%m%d%H%M') + "\n")
            f.close()
        return logfile_name
    except Exception as e:
        logger.debug("sendLog_ftps error. :" + str(e))
        _file.close()
        _ftps.quit()
        raise

def send_ftps(file_name, dir_path): #エラー処理 will be raise to main()
    try:
        logger.info("ftps accessing"+ archive_server)
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
        _ftps.login(userID, pw)
        _ftps.prot_p() #データ接続をセキュアにする

        _file = open(dir_path + '/' + file_name, 'rb') #'rb'means read as binary mode.
        # アップロードが成功したらファイルは削除。2017/06/23

        _ftps.cwd('/seasonShots/' + put_directory) #アップロード先ディレクトリに移動.ロリポップの場合、webルートに入ってくる
        logger.info('change directory to: /seasonShots/' + put_directory)
        _ftps.storbinary('STOR ' + file_name, _file)
        _file.close()
        _ftps.quit()
        logger.info("Upload finished with no error")

    except Exception as e:
        logger.debug("send(picture)_ftps error. :" + str(e))
        _file.close()
        _ftps.quit()
        raise

