import mysql.connector
from flask import current_app, g
import os
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
                    user = os.environ['DB_USER'],
                    password = os.environ['DB_PASSWORD'],
                    host = os.environ['DB_HOST'],
                    port = os.environ['DB_PORT'],
                    database = os.environ['DB_DATABASE']
                    )
    # DBの接続確認
    if not g.db.is_connected():
        raise Exception("MySQLサーバへの接続に失敗しました")
    else:
        print("MySQLサーバとの接続に成功しました")

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
