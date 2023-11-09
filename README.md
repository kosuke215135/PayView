# PayView
## ローカルでの実行方法
* 必要なライブラリをインストールします。
    * 任意のpython仮想環境等で`pip install -r requirements.txt`を実行
* ローカルのmysqlにてデータベースとテーブルを作成する
    * mysqlのコンソールに入り`source mysql_query.sqlへの絶対パス`を実行
* `./flask_app/app/.env_template`ファイルを参考に`./flask_app/app/.env`ファイルを作成する
* `cd ./flask_app/app`でappディレクトリまで移動
* `gunicorn -w 4 -b 127.0.0.1:5000 --preload "wsgi:create_app()"`を実行するとアプリが起動できる。
    * `5000`の部分は任意のポート番号を指定できる
    * `-w 4`の部分はワーカープロセス数を指定しているので、任意のものを入れてください
