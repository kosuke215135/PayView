# PayView

このリポジトリは、`PayView` というWebアプリケーションのソースコードです。  
ローカル環境での実行に必要な手順や設定方法をまとめています。

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

PayView は、決済や取引履歴を可視化・管理するためのWebアプリケーションです。  
このドキュメントではローカルで動作させるための手順を説明します。

---

## 動作環境

- Python 3.x
- MySQL
- Pip / pipenv / virtualenvなどPython仮想環境ツール（任意）

---

## インストール & セットアップ

### 必要なライブラリのインストール

1. 任意の Python 仮想環境を作成・有効化します（例：venv、pipenv など）。
2. リポジトリをクローンまたはダウンロードします。
3. `requirements.txt`を用いてライブラリをインストールします:
   ```bash
   pip install -r requirements.txt
   ```

## データベース設定
1. ローカルの MySQL でデータベースを用意します。
2. mysql_query.sql を用いてテーブルを作成します:
   ```bash
   source /path/to/mysql_query.sql
   ```
   ※ /path/to/mysql_query.sql の部分を実際のファイルパスに置き換えてください。

## 環境変数ファイルの準備
1. ./flask_app/app/.env_template を参考にしながら、同ディレクトリに .env を作成します。
2. .env 内で MySQL の接続先や必要な設定を行います。

## アプリの起動
1. cd ./flask_app/app でアプリのディレクトリに移動します。
2. Gunicorn を使ってアプリを起動します:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:5000 --preload "wsgi:create_app()"
   ```
   * -b 127.0.0.1:5000 はバインド先とポート番号です。必要に応じて変更してください。
   * -w 4 はワーカープロセス数を指定しています。環境に合わせて適宜変更してください。

アプリが起動すると、指定したポート番号（上記の例では 5000）でローカルホストにアクセスできるようになります。

## ライセンス
本プロジェクトのライセンスは MIT License を想定しています（必要に応じて書き換えてください）。
詳細は LICENSE をご覧ください。
