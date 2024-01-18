from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
import os
from dotenv import load_dotenv
import googlemaps
from db import get_db
from datetime import datetime

# .envファイルの内容を読み込見込む
load_dotenv()

LIMIT_EXE_USER_QUERY_NUM = 5

bp = Blueprint('user_add', __name__, url_prefix='/user-add')


@bp.route("/add-shop", methods=['POST'])
def add_shop():
    shop_name = request.form["shop_name"]
    shop_address = request.form["address"]

    db = get_db()
    cur = db.cursor(dictionary=True)

    # ユーザーの1日に追加できる数を制限する
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # google以外の認証も今後追加されるかもしれないのでuser_idはstr型でDB上に管理しておく
    user_id = str(session.get('user_id'))
    cur.execute("select count(*) from user_exe_queries where (user_id=%s) and (%s >= DATE_SUB(NOW(),INTERVAL 24 HOUR)) ",
                (user_id, current_date))
    num_exe_user_query_today = cur.fetchall()[0]['count(*)']
    print(num_exe_user_query_today)

    if num_exe_user_query_today >= LIMIT_EXE_USER_QUERY_NUM:
        flash("1日にお店を追加する件数を越えています")
        return redirect(url_for("render_map"))


    if (shop_name == "" or shop_address == ""):
        flash("値が入力されていません")

        return redirect(url_for("render_map"))

    try:
        gm = googlemaps.Client(key=os.environ['ADD_SHOP_API_KEY'])

        res_shop_name = gm.geocode(shop_name)
        res_shop_address = gm.geocode(shop_address)

        lat_lnb_from_shop_name = res_shop_name[0]['geometry']['location']
        lat_lnb_from_shop_address = res_shop_address[0]['geometry']['location']
    except:
        flash("このお店はgoogle mapに登録されていません")
        return redirect(url_for("render_map"))


    #存在する店かどうか確認するため、店名と住所で取得した緯度経度を比較する
    if (round(lat_lnb_from_shop_name['lat'],3) != round(lat_lnb_from_shop_address['lat'],3) 
        or round(lat_lnb_from_shop_name['lng'],3) != round(lat_lnb_from_shop_address['lng'],3)):
        flash("このお店はgoogle mapに登録されていません")

        return redirect(url_for("render_map"))
    
    try:
        cur.execute("insert into shops (name, latitude, longitude) values (%s, %s, %s);",
                    (shop_name, lat_lnb_from_shop_name['lat'], lat_lnb_from_shop_name['lng']))

        query_content = f"{user_id}のユーザーが{shop_name}というお店を追加しました"
        cur.execute("insert into user_exe_queries (user_id, query_content, exe_time) values (%s, %s, %s)",
                (user_id, query_content, current_date))

        db.commit()
    except:
        flash("このお店はすでに追加されているか、入力した値が正しくありません")
        return redirect(url_for("render_map"))

    flash("お店を追加できました") 
    return redirect(url_for("render_map"))
