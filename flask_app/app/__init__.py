from flask import Flask,render_template
import os
from flask import request
from db import get_db
import random


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


    @app.route("/detail/<int:shop_id>")
    def detail(shop_id):
        db = get_db()
        cur = db.cursor(dictionary=True)
        query = f"select * from shops where shop_id = {shop_id};"
        cur.execute(query) 
        shop_name = cur.fetchall()[0]["name"]
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
        for i in range(len(payments_name_list)):
            if i == len(payments_name_list)-1:
                payments_str = payments_str + payments_name_list[i]["name"]
                continue
            payments_str = payments_str + payments_name_list[i]["name"] + ", "
        return render_template("detail.html", shop_detail=[shop_id, shop_name, payments_str])

    return app



