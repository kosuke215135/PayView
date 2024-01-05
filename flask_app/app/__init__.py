from flask import Flask, render_template, session, redirect, url_for
import os
from flask import request
from db import get_db
import random
from datetime import timedelta #時間情報を用いるため
from calculation_location import location_distance, get_distanced_lat_lng, conversion_km_or_m
import secrets
import string


this_dir_path = os.path.dirname(os.path.abspath(__file__))

BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"

DROP_DOWN_DISTANCE = ["1km", "3km", "5km", "10km", "すべて"]

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

            result = get_distanced_lat_lng(user_latitude, user_longitude, 3)
            n = str(result["n"])
            e = str(result["e"])
            s = str(result["s"])
            w = str(result["w"])
                    
            # 3km以内のお店だけをデータベースから指定
            db = get_db()
            cur = db.cursor(dictionary=True)
            query = "select * from shops where ("+n+">latitude and latitude>"+s+") and ("+e+">longitude and longitude>"+w+");"
            cur.execute(query)
            shops = cur.fetchall()

            shops_and_payments = []
            for shop_dict in shops:
                distance = location_distance(user_latitude, user_longitude, shop_dict["latitude"], shop_dict["longitude"])
                shop_list = [shop_dict["shop_id"], shop_dict["name"], distance]
                shops_and_payments.append(shop_list)

            # 距離(distance)でソートする
            shops_and_payments.sort(key=lambda x: x[2])

            #見やすいようにkmかmに変換する
            shops_and_payments = list(map(conversion_km_or_m, shops_and_payments)) 

            for i in range(len(shops_and_payments)):
                shop_id = shops_and_payments[i][0]
                join_query = f"""
                    select 
                    payment_services.name 
                    from can_use_services 
                    inner join 
                    payment_services 
                    on can_use_services.payment_id = payment_services.payment_id 
                    where can_use_services.shop_id = {shop_id} 
                """
                cur.execute(join_query)
                payments_name_list = cur.fetchall() 
                payments_str = ""
                for l in range(len(payments_name_list)):
                    if l == len(payments_name_list)-1:
                        payments_str = payments_str + payments_name_list[l]["name"]
                        continue
                    payments_str = payments_str + payments_name_list[l]["name"] + ", "
                shops_and_payments[i].append(payments_str)


            #決済サービスタグを追加する。
            def get_payment_service_names(group_id):
                cur.execute("""
                    SELECT name
                    FROM payment_services
                    WHERE payment_group = %s
                """, (group_id,))
                return [item["name"] for item in cur.fetchall()]

            barcode_names = get_payment_service_names(BARCODE_GROUP)
            credit_names = get_payment_service_names(CREDIT_GROUP)
            electronic_money_names = get_payment_service_names(ELECTRONIC_MONEY_GROUP)
            
            #タグを追加する.
            tag_query = "select * from tags;"
            cur.execute(tag_query)
            tag_id_name_list = cur.fetchall()
            # よく使われるタグtop5
            commonly_tag = ['スーパー', '食堂', '居酒屋', 'ラーメン', 'カフェ']
            tag_commonly_used_list = []
            for tag_id_name in tag_id_name_list:
                if tag_id_name['name'] in commonly_tag:
                    tag_id_name_list.remove(tag_id_name)
                    tag_commonly_used_list.append(tag_id_name)
            
            tag_name = None #serch_shopのsearch_result関数で同じtop.htmlを表示している。その際、tag_nameが必要になるので、こちらではダミーの変数を使っている。
            search_strings = None #serch_shopのtext_search関数で同じtop.htmlを表示している。その際、search_stringsが必要になるので、こちらではダミーの変数を使っている。

            return render_template("top.html", shops_and_payments=shops_and_payments, tag_id_name_list=tag_id_name_list, tag_name=tag_name, barcode_names=barcode_names, credit_names=credit_names, electronic_money_names=electronic_money_names, tag_commonly_used_list=tag_commonly_used_list, search_strings=search_strings, DROP_DOWN_DISTANCE=DROP_DOWN_DISTANCE)

            
    @app.route("/detail/<string:os>/<int:shop_id>")
    def detail(os, shop_id):
        db = get_db()
        cur = db.cursor(dictionary=True)
        query = f"select * from shops where shop_id = {shop_id};"
        cur.execute(query) 
        shop_name = cur.fetchall()[0]["name"]
        join_query = f"""
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
            where can_use_services.shop_id = {shop_id} 
        """
        cur.execute(join_query)
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
                
        #決済サービスタグを追加する。
        def get_payment_service_names(group_id):
            cur.execute("""
                SELECT name
                FROM payment_services
                WHERE payment_group = %s
            """, (group_id,))
            return [item["name"] for item in cur.fetchall()]

        barcode_names = get_payment_service_names(BARCODE_GROUP)
        credit_names = get_payment_service_names(CREDIT_GROUP)
        electronic_money_names = get_payment_service_names(ELECTRONIC_MONEY_GROUP)
            
        #タグを追加する.
        tag_query = "select * from tags;"
        cur.execute(tag_query)
        tag_id_name_list = cur.fetchall()
        # よく使われるタグtop5
        commonly_tag = ['スーパー', '食堂', '居酒屋', 'ラーメン', 'カフェ']
        tag_commonly_used_list = []
        for tag_id_name in tag_id_name_list:
            if tag_id_name['name'] in commonly_tag:
                tag_id_name_list.remove(tag_id_name)
                tag_commonly_used_list.append(tag_id_name)

        return render_template("detail.html", shop_name=shop_name, barcode_payments=barcode_payments, credit_payments=credit_payments, electronic_money_payments=electronic_money_payments, tag_id_name_list=tag_id_name_list, barcode_names=barcode_names, credit_names=credit_names, electronic_money_names=electronic_money_names, tag_commonly_used_list=tag_commonly_used_list, DROP_DOWN_DISTANCE=DROP_DOWN_DISTANCE)

    return app



