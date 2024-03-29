# sendAllDataPicture
sendAllDataPictureはRaspberry Pi Python プログラム
Raspberry Pi 側に組み込んで使うデータ送信プログラム。
指定時間（毎正時：変更可）になったら起動し、写真、気象データをサーバーに送り込む。

**事前準備**

- pip install retry #リトライ実行のライブラリ
	rootユーザーも使えるように $ sudo pip install retry
- Raspberry Pi OSにはRAM Disk化などの事前準備を行う

**システム概要**

 - 林製作の電源コントロール基板をつかって、定時の動作起動、動作終了後には電源をオフにする。
 
 	***使い方***
	$ sudo /usr/sbin/i2cset -y 1 0x40 30 2 i #30秒後にシャットダウン、10分後に起動
	$ sudo poweroff

 - Raspberry Piにカメラ、温度・湿度・気圧（内・外）、水深、土中温度、土中湿度、日照センサーをつなぎ、データ取得
 - 専用回線（3G、LTE）を使いSoracomにデータ送信
	 - これによりセキュリティ確保
 - 里山イニシアチブ保有のサーバーにデータ送信
 - 写真はTimelapsビューア送出
 - データの可視化はAmbidataにてグラフ化

![システム全体の構成図](https://github.com/haya-sann/sendAllDataPicture/blob/master/imgs/TotalSystemConfigulation.png)
メインのプログラムは：
[sendBMEDataToIM_periodically.py](https://github.com/haya-sann/sendAllDataPicture/blob/master/sendIM/sendBMEDataToIM_periodically.py)

かわごえ里山の「田んぼカメラ」2号機のデプロイプログラム（2021/08/01再稼働）

パラメータ変更により以下の各項目の設定が可能
 - 写真撮影の開始時刻、終了時刻
 - データ取得間隔
 - 実行モード、debugモードの変更
 - システムの起動プログラムの書き換え・更新

以下の各ログを管理者にメールするとともに田んぼカメラサーバーに送信
 - syslog
 - boot.log
  
**実際の動作状況はこちら：**

2号機：スライドショー（
https://ciao-kawagoesatoyama.ssl-lolipop.jp/seasonShots/dailySlideShow_v7.php
）

気象データ：（
https://ciao-kawagoesatoyama.ssl-lolipop.jp/IM/index.html
）
> Written with [StackEdit](https://stackedit.io/).


ライセンスはオープンソースのMITライセンスとします。
「改変でも、再配布でも、商用利用でも、有料販売でも、どんなことにでも自由に無料で使うことができます」

