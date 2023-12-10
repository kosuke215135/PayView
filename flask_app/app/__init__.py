from flask import Flask, render_template, session
import os
from flask import request
from db import get_db
import random
from datetime import timedelta #時間情報を用いるため
import math

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
    

    # 現在地からお店まで〜kmか出力する関数
    def location_distance(user_latitude, user_longitude, store_latitude, store_longitude):
        # 地球の半径（キロメートル）
        R = 6371.0

        # 緯度経度をラジアンに変換
        lat1 = math.radians(user_latitude)
        lon1 = math.radians(user_longitude)
        lat2 = math.radians(store_latitude)
        lon2 = math.radians(store_longitude)

        # 緯度と経度の差
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        # ハーヴァーサイン公式
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # 距離
        distance = R * c

        return distance
    
    def get_distanced_lat_lng(lat, lng, distance):
        R = math.pi / 180  # 円周率をラジアンに変換
        earth_radius = 6371  # 地球の半径（キロメートル）
        kilometer_per_degree = R * earth_radius  # 1度あたりのキロメートル
        degree_per_kilometer = 1 / kilometer_per_degree  # 1キロメートルあたりの度
        diff = distance * degree_per_kilometer  # 指定された距離を角度に変換
        return {'n': lat + diff, 'e': lng + diff, 's': lat - diff, 'w': lng - diff}

    # jsからhttp経由のPOST方式で、現在地のデータを受け取る。 by kouya
    @app.route('/send-location', methods=['POST'])
    def receive_location():
        location_data = request.json
        user_latitude = location_data["latitude"]
        user_longitude = location_data["longitude"]
        
        
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
        
        latitude_longitude_list = []
        for shop_dict in shops:
            latitude_longitude = [shop_dict["latitude"], shop_dict["longitude"]]
            latitude_longitude_list.append(latitude_longitude)
        
        distance_list = []
        # 距離を出す
        for latitude_longitude in latitude_longitude_list:
            store_latitude = latitude_longitude[0]
            store_longitude = latitude_longitude[1]
            distance = location_distance(user_latitude, user_longitude, store_latitude, store_longitude)
            distance_list.append(distance)
        return render_template("top.html", distance_list=distance_list)
    
    @app.route("/")
    def top():
        db = get_db()
        cur = db.cursor(dictionary=True)
        query = "select * from shops;"
        cur.execute(query)
        shops = cur.fetchall()
        shops_and_payments = []
        for shop_dict in shops:
            shop_list = [shop_dict["shop_id"], shop_dict["name"]]
            shops_and_payments.append(shop_list)
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



