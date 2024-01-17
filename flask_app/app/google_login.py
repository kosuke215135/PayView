import requests
import json
from flask import Flask, request, redirect, Blueprint, url_for, session, g
from oauthlib.oauth2 import WebApplicationClient
from dotenv import load_dotenv
import os

# .envファイルの内容を読み込見込む
load_dotenv()

GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']

GOOGLE_DISCOVERY_URL = (
    'https://accounts.google.com/.well-known/openid-configuration'
)

bp = Blueprint('google_login', __name__, url_prefix='/google-login')

client = WebApplicationClient(GOOGLE_CLIENT_ID)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@bp.route('/g_login')
def g_login():
    # ログイン後もログインを行った画面に遷移する
    from_url = request.referrer
    session['from'] = from_url

    # 認証用のエンドポイントを取得
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg['authorization_endpoint']

    # ユーザのID,メールアドレス、プロファイルのリクエスト
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri = (request.url_root)[:-1] + url_for("google_login.g_callback"),
        scope=['openid', 'email', 'profile'],
    )

    return redirect(request_uri)


@bp.route('/callback')
def g_callback():

    # Googleから返却された認証コードを取得する
    code = request.args.get("code")

    # トークンを取得用のエンドポイントを取得
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    print(request.url)
    print(request.base_url)
    # トークン取得用の情報を生成
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )

    # リクエスト(id_tokenの取得)
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # トークンをparse
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # 辞書に変換
    userinfo_response = userinfo_response.json() 

    # 認証情報をsessionに保存
    session['user_id'] = userinfo_response["sub"]
    session['user_name'] = userinfo_response["name"]
    session['user_email'] = userinfo_response["email"]
    session["user_picture_url"] = userinfo_response["picture"]

    # 元いた画面に遷移する
    return redirect(session['from'])



# gはリクエストごとに変数を保存できる。主に表示に用いる
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    user_name = session.get('user_name')
    user_email = session.get('user_email')
    user_picture_url = session.get('user_picture_url')

    if user_id is None:
        g.user = None
    else:
        g.user = {'user_name': user_name, 'user_email': user_email, 'user_picture_url':user_picture_url}


@bp.route('/g-logout')
def g_logout():
    from_url = request.referrer
    session.clear()

    return redirect(from_url)




