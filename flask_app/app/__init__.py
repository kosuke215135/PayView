from flask import Flask, render_template, session
import os
from flask import request
from db import get_db
import random
from datetime import timedelta #時間情報を用いるため
from calculation_location import location_distance, get_distanced_lat_lng, conversion_km_or_m
this_dir_path = os.path.dirname(os.path.abspath(__file__))


def create_app():
    #Flaskオブジェクトの生成
    app = Flask(__name__)

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
    @app.route("/top", methods=['POST'])
    def top():
        user_latitude = float(request.form["latitude"])
        user_longitude = float(request.form["longitude"])
        
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

        #タグを追加する.
        tag_query = "select * from tags;"
        cur.execute(tag_query)
        tag_id_name_list = cur.fetchall()
        random.shuffle(tag_id_name_list) #ランダムに表示する
        tag_id_name_list = tag_id_name_list[:6] #先頭の6個までを表示

        tag_name = None #serch_shopのsearch_result関数で同じtop.htmlを表示している。その際、tag_nameが必要になるので、こちらではダミーの変数を使っている。
        print("execute top()")
        return render_template("top.html", shops_and_payments=shops_and_payments, tag_id_name_list=tag_id_name_list, tag_name=tag_name)


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
                    scheme_list = [payment["name"], payment["iOS_scheme"]]
                    scheme_data.append(scheme_list)
                else:
                    scheme_list = [payment["name"], None]
                    scheme_data.append(scheme_list)
            elif os == "Android":
                if payment["Android_scheme"] != "":
                    scheme_list = [payment["name"], payment["Android_scheme"]]
                    scheme_data.append(scheme_list)
                else:
                    scheme_list = [payment["name"], None]
                    scheme_data.append(scheme_list)
            else:
                scheme_list = [payment["name"], None]
                scheme_data.append(scheme_list)

        return render_template("detail.html", shop_detail=[shop_id, shop_name, payments_name_list, scheme_data])

    return app



