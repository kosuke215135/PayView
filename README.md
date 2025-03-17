# PayView

enpitで開発したwebアプリ

---

## 目次

1. [概要](#概要)  
2. [動作環境](#動作環境)  
3. [インストール & セットアップ](#インストール--セットアップ)  
   - [必要なライブラリのインストール](#必要なライブラリのインストール)  
   - [データベース設定](#データベース設定)  
   - [環境変数ファイルの準備](#環境変数ファイルの準備)  
4. [アプリの起動](#アプリの起動)  
5. [ライセンス](#ライセンス)  
6. [連絡先](#連絡先)  

---

## 概要

このwebアプリは消費者向けで、現在地から利用可能な店舗を検索し、その店舗で使用できる決済サービスを事前に確認できる機能を備えている。 ユーザーは検索機能を利用して登録されているお店を調べることができ、さらに「食べログ」とは異なり、利用可能な決済サービスのボタンを押すことで、対応する決済アプリへ直接移動することが可能。 また、ユーザー自身が新たな店舗情報や決済サービスの対応状況を追加できる仕組みも備えている。

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

## データベース設定
1. ローカルの MySQL でデータベースを用意する。
2. mysql_query.sql を用いてテーブルを作成:
   ```bash
   source /path/to/mysql_query.sql
   ```
   ※ /path/to/mysql_query.sql の部分を実際のファイルパスに置き換える。

## 環境変数ファイルの準備
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
本プロジェクトのライセンスは MIT License を想定しています（必要に応じて書き換えてください）。
詳細は LICENSE をご覧ください。
