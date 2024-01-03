from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from calculation_location import location_distance, get_distanced_lat_lng,conversion_km_or_m
from db import get_db
import random
import MeCab
import neologdn

bp = Blueprint('search_shop', __name__, url_prefix='/search-shop')

BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"
# 検索で使用する品詞を記述
USE_PART_OF_SPEECH = ["名詞", "動詞", "形容詞", "副詞"]
# 検索結果がこれ以下の件数である場合少ないと判断する
MIN_NUM_SEARCH_RESULTS = 0

# 形態素解析の結果をlistにして返す関数
def mecab_list(text):
    tagger = MeCab.Tagger("-Ochasen")
    tagger.parse('')
    node = tagger.parseToNode(text)
    word_class = []
    while node:
        word = node.surface
        wclass = node.feature.split(',')
        if wclass[0] != u'BOS/EOS':
            if wclass[6] == None:
                word_class.append((word,wclass[0],wclass[1],wclass[2],""))
            else:
                word_class.append((word,wclass[0],wclass[1],wclass[2],wclass[6]))
        node = node.next
    return word_class


# 類似語や省略形が含まれていれば、検索に適しているワードを返す
# その紐づけはsynonymsテーブルで行われている
def search_synonym(search_strings_list):
    db = get_db()
    cur = db.cursor(dictionary=True) 
    return_list = []
    for i in range(len(search_strings_list)):
        query = f"select * from synonyms  "
        tmp_list = []
        
        for j in range(len(search_strings_list[i])):
            if j == 0:
                query += f" where synonym='{search_strings_list[i][j]}' "
            else:
                query += f" or synonym='{search_strings_list[i][j]}' "
            # 検索したままのワードも入れておく
            tmp_list.append(search_strings_list[i][j])

        cur.execute(query)
        sql_result_list = cur.fetchall()
        for j in range(len(sql_result_list)):
            tmp_list.append(sql_result_list[j]["original_word"])
        
        return_list.append(tmp_list)

    return return_list


# 検索するためのsqlを発行する関数(n-gram)
# 二重リストを受け取り3つの文字列を返す
def create_sql_search_n_gram(search_strings_list, operator="and"):

    query_to_shops = "select * from shops "
    query_to_payment_services = "select * from payment_services "
    query_to_tags = "select * from tags "
    query_common_part = ""

    print(search_strings_list)
    for i in range(len(search_strings_list)):
        if i == 0:
            query_common_part += " where "
        else:
            query_common_part += f" {operator} "
            
        for j in range(len(search_strings_list[i])):
            #最初のクエリであれば以下を追加する
            if j == 0:
                query_common_part += " match (name) against (' "

            search_string = search_strings_list[i][j]
            query_common_part += search_string

            #最後のクエリであれば以下を追加する
            if j == len(search_strings_list[i]) - 1:
                query_common_part += " ' in boolean mode) "

    query_to_shops += query_common_part; query_to_payment_services += query_common_part; query_to_tags += query_common_part; 
    return query_to_shops, query_to_payment_services, query_to_tags


# like句での検索をを行うsqlを発行する関数
def create_sql_search_like(search_words):
    query_to_shops = "select * from shops "
    query_to_payment_services = "select * from payment_services "
    query_to_tags = "select * from tags "
    query_common_part = ""
    
    for i in range(len(search_words)):
        if i == 0:
            query_common_part += " where "
        else:
            query_common_part += " and "
        query_common_part += f" name like '%{search_words[i]}%' "
    
    query_to_shops += query_common_part; query_to_payment_services += query_common_part; query_to_tags += query_common_part; 
    return query_to_shops, query_to_payment_services, query_to_tags


# 検索を実行する関数
def execut_sql_search(query_to_shops, query_to_payment_services, query_to_tags):
    db = get_db()
    cur = db.cursor(dictionary=True)

    #検索ワードに関連するお店を調べる
    print(query_to_shops)
    cur.execute(query_to_shops)
    search_result_shops = cur.fetchall()

    #検索ワードに関連する決済サービスを調べる
    cur.execute(query_to_payment_services)
    search_result_payment_services = cur.fetchall()

    # 検索でヒットした決済サービスが使用できるお店を調べる
    for search_result_payment_service in search_result_payment_services:
        payment_id = search_result_payment_service["payment_id"]
        tmp_query = f"select * from shops inner join can_use_services on shops.shop_id = can_use_services.shop_id where can_use_services.payment_id='{payment_id}' "
        cur.execute(tmp_query)
        search_result_shops += cur.fetchall()

    #検索ワードに関連するタグを調べる
    cur.execute(query_to_tags)
    search_result_tags = cur.fetchall()

    # 検索でヒットしたタグがつけられているお店を調べる
    for search_result_tag in search_result_tags:
        tag_id = search_result_tag["tag_id"]
        tmp_query = f"select * from shops inner join allocated_tags on shops.shop_id = allocated_tags.shop_id where allocated_tags.tag_id='{tag_id}' "
        cur.execute(tmp_query)
        search_result_shops += cur.fetchall()
    
    return search_result_shops

#リスト内の辞書の重複を削除する関数
def get_unique_list(seq):
    already_append_shop_id = []
    not_duplication = []
    for dic in seq:
        if dic["shop_id"] in already_append_shop_id:
            continue
        else:
            already_append_shop_id.append(dic["shop_id"])
            not_duplication.append(dic)
    return not_duplication


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
    db = get_db()
    cur = db.cursor(dictionary=True)

    #Cookieからユーザーの現在地を取得
    user_latitude = session.get("user_latitude")
    user_longitude = session.get("user_longitude") 

    # htmlから検索を掛ける文字列を取得する
    # 半角スペースや全角スペースごとに区切る
    search_strings = request.form["search_strings"]
    search_words = search_strings.split()

    # neologdnで検索ワードの前処理を行う
    for i in range(len(search_words)):
        search_words[i] = neologdn.normalize(search_words[i])

    #検索ワードを分かち書きしたものをそれぞれlistとして保持する2重リスト
    search_strings_list = []
    
    for search_word in search_words:
        # 検索ワードごとに形態素解析を行う
        morpheme_list = mecab_list(search_word)
        tmp_list = []
        for morpheme in morpheme_list:
            part_of_speech = morpheme[1]
            # 分かち書きした単語の品詞によって、検索で使用するかどうか判定する
            if part_of_speech in USE_PART_OF_SPEECH:
                tmp_list.append(morpheme[0])
        # 検索に使える品詞がない場合はcontinue
        if len(tmp_list) == 0:
            continue
        search_strings_list.append(tmp_list)

    print(search_strings_list)
    # 検索に使えるwordが無い場合は結果を空にしておく 
    # 距離の検索と文字列検索を兼ねているため、文字列が何も入力されていない場合は距離だけの絞り込みを行う
    if (len(search_strings_list) == 0) and (search_strings != ''):
        search_result_shops = []
    else:
        # 類似語や省略形があれば、検索に適した単語も検索リストに加える
        search_strings_list = search_synonym(search_strings_list)
        # 検索を行うためにsqlを発行する
        query_to_shops, query_to_payment_services, query_to_tags = create_sql_search_n_gram(search_strings_list)
        # 検索を行う
        search_result_shops = execut_sql_search(query_to_shops, query_to_payment_services, query_to_tags)

        # 検索件数が極端に少ない場合,検索ワードごとにlike句での検索を再び行う
        if len(search_result_shops) <= MIN_NUM_SEARCH_RESULTS:
            like_query_to_shops, like_query_to_payment_services, like_query_to_tags = create_sql_search_like(search_words)
            search_result_shops += execut_sql_search(like_query_to_shops, like_query_to_payment_services, like_query_to_tags)

        # まだ検索件数が極端に少ない場合,OR検索を行う
        if len(search_result_shops) <= MIN_NUM_SEARCH_RESULTS:
            or_query_to_shops, or_query_to_payment_services, or_query_to_tags = create_sql_search_n_gram(search_strings_list, operator="or")
            search_result_shops += execut_sql_search(or_query_to_shops, or_query_to_payment_services, or_query_to_tags)

    # 検索結果の重複を削除
    search_result_shops = get_unique_list(search_result_shops)
    
    shops_and_payments = []
    for shop_dict in search_result_shops:
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
