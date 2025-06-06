# PayView

enpitで開発したwebアプリ


## 目次

1. [アプリイメージ](#アプリイメージ)
2. [コンセプト](#コンセプト)  
3. [エレベーターピッチ](#エレベーターピッチ)  
4. [主な機能](#主な機能)  
5. [動作環境](#動作環境)  
6. [インストール & セットアップ](#インストール--セットアップ)  
   - [必要なライブラリのインストール](#必要なライブラリのインストール)  
   - [データベース設定](#データベース設定)  
   - [環境変数ファイルの準備](#環境変数ファイルの準備)  
7. [アプリの起動](#アプリの起動)  
8. [ライセンス](#ライセンス)  


## アプリイメージ

![Image](https://github.com/user-attachments/assets/ddf168a2-9e18-4154-8f7e-6a81f27b64e1)


## コンセプト
「このお店、あの決済サービス使えるかな？」 <br>
そんな疑問に答えるのが、PayView です。

## エレベーターピッチ

「　行ってみたい飲食店の決済サービスを事前に確認　」したい　<br>
「　消費者　」向けの<br>
「　PayView　」というプロダクトは<br>
「　自分が利用したい店舗の決済サービスが一目でわかるwebアプリ　」です。<br>
これは「　現在地から利用する店舗を調べ、使用できる決済サービスを確認する　」でき、<br>
「　食べログ　」とは違って<br>
「　使用できる決済サービスを見て、その決済アプリに飛ぶことができる機能　」が備わっている。


## 主な機能

- 現在地周辺の飲食店を表示
- 各飲食店の決済サービスの確認
- 決済サービスのボタンを押すと、その決済サービスのアプリに飛ぶことができる(iOS, Androidのみ)
- 検索機能
  - 店名
  - 決済サービス名
  - 距離絞り込み検索
- ユーザー自身がお店の決済情報を追加可能


---

## 動作環境

- Python 3.x
- MySQL
- Pip

---

## インストール & セットアップ

### 必要なライブラリのインストール
1. リポジトリをクローンまたはダウンロードする。
2. `requirements.txt`を用いてライブラリをインストールする:
   ```bash
   pip install -r requirements.txt
   ```

### データベース設定
1. ローカルの MySQL でデータベースを用意する。
2. mysql_query.sql を用いてテーブルを作成:
   ```bash
   source /path/to/mysql_query.sql
   ```
   ※ /path/to/mysql_query.sql の部分を実際のファイルパスに置き換える。

### 環境変数ファイルの準備
1. ./flask_app/app/.env_template を参考にしながら、同ディレクトリに .env を作成。
3. .env 内で MySQL の接続先や必要な設定を行う。

## アプリの起動
1. cd ./flask_app/app でアプリのディレクトリに移動。
2. Gunicorn を使ってアプリを起動:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:5000 --preload "wsgi:create_app()"
   ```
   * -b 127.0.0.1:5000 はバインド先とポート番号。必要に応じて変更可能。
   * -w 4 はワーカープロセス数を指定。環境に合わせて適宜変更可能。

アプリが起動すると、指定したポート番号（上記の例では 5000）でローカルホストにアクセスできるようになる。

## ライセンス
本プロジェクトのライセンスは GNU General Public License (GPL 2.0) を想定しています。
