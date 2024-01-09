from flask import Flask, render_template, session, redirect, url_for
import os
from flask import request
from db import get_db
import random
from datetime import timedelta #時間情報を用いるため
from calculation_location import location_distance, get_distanced_lat_lng, conversion_km_or_m, accurately_determine_distance
from create_display_common_data import get_category_data, get_can_use_services
import secrets
import string


this_dir_path = os.path.dirname(os.path.abspath(__file__))

CASH_GROUP = "01PG"
BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"

DROP_DOWN_DISTANCE = [1, 3, 5, 10, -1]

DEFAULT_SEARCH_DISTANCE_KM = 1

#シークレットキーを作成
def get_random_string(length):
    pass_chars = string.ascii_letters + string.digits
    random_str = ''.join(secrets.choice(pass_chars) for x in range(length))
    return random_str

SECRET_KEY = get_random_string(12)

def create_app():
    #Flaskオブジェクトの生成
    app = Flask(__name__)

    #シークレットキーを登録
    app.secret_key = SECRET_KEY

    import db
    db.init_app(app)

    import insert_shop_data
    app.register_blueprint(insert_shop_data.bp)

    import search_shop
    app.register_blueprint(search_shop.bp)
    
    @app.route("/")
    def loading():
        return render_template("loading.html")


    # jsからhttp経由のPOST方式で、現在地のデータを受け取る。
    @app.route("/top", methods=['GET','POST'])
    def top():
        if request.method == "POST":
            user_latitude = float(request.form["latitude"])
            user_longitude = float(request.form["longitude"])
            # 位置情報をCookieに保存
            session['user_latitude'] = user_latitude
            session['user_longitude'] = user_longitude
            return redirect(url_for('top'))

        elif request.method == "GET":
            #Cookieからユーザーの現在地を取得
            user_latitude = session.get("user_latitude")
            user_longitude = session.get("user_longitude") 

            result = get_distanced_lat_lng(user_latitude, 
                                           user_longitude, 
                                           DEFAULT_SEARCH_DISTANCE_KM)
            n = str(result["n"])
            e = str(result["e"])
            s = str(result["s"])
            w = str(result["w"])
                    
            # 1km以内のお店だけをデータベースから指定
            db = get_db()
            cur = db.cursor(dictionary=True)
            query = f"""
                select 
                * 
                from 
                shops 
                where ({n}>latitude and latitude>{s}) 
                and ({e}>longitude and longitude>{w});"""
            cur.execute(query)
            shops = cur.fetchall()

            shops_and_payments = []
            for shop_dict in shops:
                distance = location_distance(user_latitude, 
                                             user_longitude, 
                                             shop_dict["latitude"], 
                                             shop_dict["longitude"])
                shop_list = [shop_dict["shop_id"], shop_dict["name"], distance]
                shops_and_payments.append(shop_list)
            
            #正確な距離制限を掛ける
            shops_and_payments = accurately_determine_distance(shops_and_payments, DEFAULT_SEARCH_DISTANCE_KM)

            # 距離(distance)でソートする
            shops_and_payments.sort(key=lambda x: x[2])

            #見やすいようにkmかmに変換する
            shops_and_payments = list(map(conversion_km_or_m, shops_and_payments)) 

            # お店で使用できる決済サービスの名前を追加する
            get_can_use_services(shops_and_payments)

            # カテゴリ欄のデータを取得する
            tag_id_name_list, cash_group, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list = get_category_data()
            
            return render_template(
                "top.html", 
                shops_and_payments=shops_and_payments, 
                tag_id_name_list=tag_id_name_list, 
                cash_group=cash_group,
                barcode_names=barcode_names, 
                credit_names=credit_names, 
                electronic_money_names=electronic_money_names, 
                tag_commonly_used_list=tag_commonly_used_list, 
                DROP_DOWN_DISTANCE=DROP_DOWN_DISTANCE, 
                selected_distance="", 
                searched_strings="")

            
    @app.route("/detail/<string:os>/<int:shop_id>")
    def detail(os, shop_id):
        db = get_db()
        cur = db.cursor(dictionary=True)
        query = "select * from shops where shop_id = %s;"
        cur.execute(query, (shop_id,)) 
        shop_name = cur.fetchall()[0]["name"]
        join_query = """
            select 
            payment_services.payment_id,
            payment_services.name,
            payment_services.payment_group,
            payment_schemes.iOS_scheme,
            payment_schemes.Android_scheme
            from can_use_services 
            inner join 
            payment_services 
            on can_use_services.payment_id = payment_services.payment_id 
            LEFT OUTER JOIN
            payment_schemes
            on
            can_use_services.payment_id = payment_schemes.payment_id
            where can_use_services.shop_id = %s
        """
        cur.execute(join_query, (shop_id,))
        payments_name_list = cur.fetchall()

        scheme_data = []
        for payment in payments_name_list:
            scheme_list=[]
            if os == "iOS":
                if payment["iOS_scheme"] != "":
                    scheme_list = [payment["name"], payment["iOS_scheme"], payment["payment_group"]]
                else:
                    scheme_list = [payment["name"], None, payment["payment_group"]]
            elif os == "Android":
                if payment["Android_scheme"] != "":
                    scheme_list = [payment["name"], payment["Android_scheme"], payment["payment_group"]]
                else:
                    scheme_list = [payment["name"], None, payment["payment_group"]]
            else:
                scheme_list = [payment["name"], None, payment["payment_group"]]
            scheme_data.append(scheme_list)

        barcode_payments = []
        credit_payments = []
        electronic_money_payments = []
        for pay_scheme in scheme_data:
            payment_group = pay_scheme[2]
            if payment_group == BARCODE_GROUP:
                barcode_payments.append(pay_scheme)
            elif payment_group == CREDIT_GROUP:
                credit_payments.append(pay_scheme)
            elif payment_group == ELECTRONIC_MONEY_GROUP or payment_group == TRANSPORTATION_GROUP:
                electronic_money_payments.append(pay_scheme)
                
        # カテゴリ欄のデータを取得する
        tag_id_name_list, cash_group, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list = get_category_data()

        return render_template(
            "detail.html", 
            shop_name=shop_name, 
            barcode_payments=barcode_payments, 
            credit_payments=credit_payments, 
            electronic_money_payments=electronic_money_payments, 
            tag_id_name_list=tag_id_name_list, 
            cash_group=cash_group,
            barcode_names=barcode_names, 
            credit_names=credit_names, 
            electronic_money_names=electronic_money_names, 
            tag_commonly_used_list=tag_commonly_used_list, 
            DROP_DOWN_DISTANCE=DROP_DOWN_DISTANCE)
    
    @app.route("/map")
    def render_map():
        return render_template("map.html")

    return app



