from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from db import get_db
import random

bp = Blueprint('search_shop', __name__, url_prefix='/search-shop')


@bp.route('/search-result/<string:tag_id>')
def search_result(tag_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    query = f"select shops.shop_id, shops.name from shops inner join allocated_tags on shops.shop_id = allocated_tags.shop_id where allocated_tags.tag_id='{tag_id}';"
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

    #タグ名を取得する
    cur.execute(f"select name from tags where tag_id = '{tag_id}'")
    tag_name = cur.fetchall()[0]["name"]

    return render_template("top.html", shops_and_payments=shops_and_payments, tag_id_name_list=tag_id_name_list, tag_name=tag_name)
