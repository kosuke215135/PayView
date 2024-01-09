from flask import Blueprint, session, request, redirect, url_for, render_template

bp = Blueprint('external_access', __name__, url_prefix='/external-access')

@bp.before_app_request
def check_have_location():
    if request.script_root == "static":
        return
    to_url = request.url
    print(to_url)
    print(request.url_root)
    if to_url == request.url_root:
        return
    # 位置情報を持ってない場合はローディング画面を挟む
    if "user_latitude" not in session or "user_longitude" not in session:
        # ダミーの位置情報をCookieに保存(何も入れないとループしてしまう)
        session['user_latitude'] = 1
        session['user_longitude'] = 1
        to_url = request.url
        return render_template("loading.html", to_url=to_url)


