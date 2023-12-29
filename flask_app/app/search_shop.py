from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from calculation_location import location_distance, get_distanced_lat_lng,conversion_km_or_m
from db import get_db
import random
import MeCab

bp = Blueprint('search_shop', __name__, url_prefix='/search-shop')

BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"

@bp.route('/search-result/<string:tag_id>')
def search_result(tag_id):
    #Cookieからユーザーの現在地を取得
    user_latitude = session.get("user_latitude")
    user_longitude = session.get("user_longitude") 
    
    result = get_distanced_lat_lng(user_latitude, user_longitude, 3)
    n = str(result["n"])
    e = str(result["e"])
    s = str(result["s"])
    w = str(result["w"])

    db = get_db()
    cur = db.cursor(dictionary=True)
    query = f"select * from shops inner join allocated_tags on shops.shop_id = allocated_tags.shop_id where (allocated_tags.tag_id='{tag_id}') and ({n}>latitude and latitude>{s}) and ({e}>longitude and longitude>{w});"
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
    
    #タグ名を取得する
    cur.execute(f"select name from tags where tag_id = '{tag_id}'")
    tag_name = cur.fetchall()[0]["name"]

    search_strings = None #serch_shopのtext_search関数で同じtop.htmlを表示している。その際、search_stringsが必要になるので、こちらではダミーの変数を使っている。

    return render_template("top.html", shops_and_payments=shops_and_payments, tag_id_name_list=tag_id_name_list, tag_name=tag_name, barcode_names=barcode_names, credit_names=credit_names, electronic_money_names=electronic_money_names, tag_commonly_used_list=tag_commonly_used_list, search_strings=search_strings)
    


@bp.route('/search-result/text-search', methods=['POST'])
def text_search():
    #Cookieからユーザーの現在地を取得
    user_latitude = session.get("user_latitude")
    user_longitude = session.get("user_longitude") 

    wakati = MeCab.Tagger("-Owakati")

    # htmlから検索を掛ける文字列を取得する
    search_strings = request.form["search_strings"]
    search_strings_list = wakati.parse(search_strings).split()
    
    query = "select * from shops"

    for i in range(len(search_strings_list)):
        if i == 0:
            query += f" where MATCH (name) AGAINST ('{search_strings_list[i]}')" 
        else:
            query += f" and MATCH (name) AGAINST ('{search_strings_list[i]}')" 


    db = get_db()
    cur = db.cursor(dictionary=True)
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

    return render_template("top.html", shops_and_payments=shops_and_payments, tag_id_name_list=tag_id_name_list, tag_name=tag_name, search_strings=search_strings)
