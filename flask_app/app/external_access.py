from flask import Blueprint, session, request, redirect, url_for, render_template

bp = Blueprint('external_access', __name__, url_prefix='/external-access')

@bp.before_app_request
def check_have_location():
    to_url = request.url
    # htmlの記述のなかのurl_for('static')で呼ばれたものに対しては実行しない
    # ルートにアクセスする場合は実行しない
    # get-locationにアクセスする場合は実行させない
    if ("static" in to_url) or (to_url == request.url_root) or ("get-location" in to_url):
        return
    # 位置情報を持っていないか、この関数が一度も実行されていない場合にローディング画面を挟む
    if "called_check_have_location" not in session or ("user_latitude" not in session or "user_longitude" not in session):
        session["called_check_have_location"] = True
        return render_template("loading.html", to_url=to_url)


