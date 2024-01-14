from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from calculation_location import location_distance, get_distanced_lat_lng,conversion_km_or_m, accurately_determine_distance
from create_display_common_data import get_category_data, get_can_use_services
from db import get_db
from db import load_api_key
import random
import MeCab
import neologdn
import json

bp = Blueprint('search_shop', __name__, url_prefix='/search-shop')

BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"
# 検索で使用する品詞を記述
USE_PART_OF_SPEECH = ["名詞", "動詞", "形容詞", "副詞"]
# 検索結果がこれ以下の件数である場合少ないと判断する
MIN_NUM_SEARCH_RESULTS = 0

DROP_DOWN_DISTANCE = [1, 3, 5, 10, -1]

DEFAULT_SEARCH_DISTANCE_KM = 1

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
        variable_tuple = ()
        for j in range(len(search_strings_list[i])):
            if j == 0:
                query += " where synonym=%s "
            else:
                query += " or synonym=%s "
            # 検索したままのワードも入れておく
            tmp_list.append(search_strings_list[i][j])
            # プレースホルダーで使用する変数を格納
            variable_tuple += (search_strings_list[i][j],)

        cur.execute(query, variable_tuple)
        sql_result_list = cur.fetchall()
        for j in range(len(sql_result_list)):
            tmp_list.append(sql_result_list[j]["original_word"])
        
        return_list.append(tmp_list)

    return return_list


# 検索するためのsqlを発行する関数(n-gram)
def create_sql_search_n_gram(search_strings_list):

    query_every_search_word = []
    variable_every_search_word = []

    for i in range(len(search_strings_list)):
        query_to_shops = "select * from shops "
        query_to_payment_services = "select * from payment_services "
        query_to_tags = "select * from tags "
        query_common_part = " where match (name) against ( %s  in boolean mode) "
        variable_tuple = ()
        tmp_strings = ""
        for j in range(len(search_strings_list[i])):
            # 変数を追加する
            tmp_strings += f" {search_strings_list[i][j]} "
            
        query_to_shops += query_common_part
        query_to_payment_services += query_common_part
        query_to_tags += query_common_part

        query_every_search_word.append([query_to_shops, 
                                        query_to_payment_services,
                                        query_to_tags])

        variable_tuple += (tmp_strings,)
        variable_every_search_word.append(variable_tuple)
        
    return query_every_search_word, variable_every_search_word


# like句での検索をを行うsqlを発行する関数
def create_sql_search_like(search_words):
    query_every_search_word = []
    variable_every_search_word = []

    for i in range(len(search_words)):
        query_to_shops = "select * from shops "
        query_to_payment_services = "select * from payment_services "
        query_to_tags = "select * from tags "
        variable_tuple = ()

        query_common_part = " where name like %s "
        variable_tuple += ('%'+search_words[i]+'%',)

        query_to_shops += query_common_part
        query_to_payment_services += query_common_part
        query_to_tags += query_common_part

        query_every_search_word.append([query_to_shops,
                                        query_to_payment_services, 
                                        query_to_tags])
        
        variable_every_search_word.append(variable_tuple)

    return query_every_search_word, variable_every_search_word


# 検索を実行する関数
def execut_sql_search(
        query_every_search_word, 
        variable_every_search_word, 
        distance_limit_sql, 
        be_all_distance, 
        be_input_search_word=True):
    """
    Args:
        query_every_search_word [[str]]: 各TableへのSQLが格納されたリストが検索ワードごとに格納されている
    
    Returns:
        [{str: x}]: 店の情報を格納しているリスト 
    """
    db = get_db()
    cur = db.cursor(dictionary=True)

    result_every_search_word = []

    for i in range(len(query_every_search_word)):
        # 各Tableへのクエリを取り出す
        query_to_shops = query_every_search_word[i][0]
        query_to_payment_services = query_every_search_word[i][1]
        query_to_tags = query_every_search_word[i][2]

        # クエリごとに変数をタプルで持っておく(プレースホルダーを使用するため)
        variable_tuple = variable_every_search_word[i]

        # 距離の指定を付け加える
        if not be_all_distance:
            if be_input_search_word:
                query_to_shops = query_to_shops + " and " +distance_limit_sql
            else:
                query_to_shops = query_to_shops + " where " +distance_limit_sql

        #検索ワードに関連するお店を調べる
        cur.execute(query_to_shops, variable_tuple)
        search_result_shops = cur.fetchall()

        #検索ワードに関連する決済サービスを調べる
        cur.execute(query_to_payment_services, variable_tuple)
        search_result_payment_services = cur.fetchall()

        # 検索でヒットした決済サービスが使用できるお店を調べる
        for search_result_payment_service in search_result_payment_services:
            payment_id = search_result_payment_service["payment_id"]
            tmp_query = f"""
                select 
                * 
                from 
                shops 
                inner join can_use_services on shops.shop_id = can_use_services.shop_id 
                where 
                can_use_services.payment_id='{payment_id}' """
            if not be_all_distance:
                # 距離の指定を付け加える
                tmp_query = tmp_query + " and " + distance_limit_sql
            cur.execute(tmp_query)
            search_result_shops += cur.fetchall()

        #検索ワードに関連するタグを調べる
        cur.execute(query_to_tags, variable_tuple)
        search_result_tags = cur.fetchall()

        # 検索でヒットしたタグがつけられているお店を調べる
        for search_result_tag in search_result_tags:
            tag_id = search_result_tag["tag_id"]
            tmp_query = f"""
                select
                * 
                from 
                shops 
                inner join allocated_tags on shops.shop_id = allocated_tags.shop_id 
                where 
                allocated_tags.tag_id='{tag_id}' """
            if not be_all_distance:
                # 距離の指定を付け加える
                tmp_query = tmp_query + " and " + distance_limit_sql
            cur.execute(tmp_query)
            search_result_shops += cur.fetchall()

        result_every_search_word.append(search_result_shops)
        
    search_result_shops = and_search_every_search_word(result_every_search_word)
    
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


def and_search_every_search_word(result_every_search_word):
    """
    Args:
        result_every_search_word [[{str: x}]]: 検索ワードごとの検索結果を格納しているリスト
    
    Returns:
        [{str: x}]: AND検索を行った後の店の情報を格納しているリスト 
    """
    already_append_shop_id = []
    for result in result_every_search_word:
        tmp_set = set()
        for re in result:
            tmp_set.add(re["shop_id"])
        already_append_shop_id.append(tmp_set)
    
    and_shop_id_set = set()

    for i in range(len(already_append_shop_id)):
        if i == 0:
            and_shop_id_set |= already_append_shop_id[i]
        else:
            and_shop_id_set &= already_append_shop_id[i]
    
    result_and_search = []
    for re in result_every_search_word[0]:
        if re["shop_id"] in and_shop_id_set:
            result_and_search.append(re)
            and_shop_id_set.remove(re["shop_id"])
    
    return result_and_search





@bp.route('/search-result/<string:payment_or_tag_id>')
def search_result(payment_or_tag_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # "決済サービス"か"タグ"かを判別する
    if payment_or_tag_id[-1] == "P":
        query = """
            select 
            * 
            from 
            shops 
            inner join can_use_services on shops.shop_id = can_use_services.shop_id 
            where can_use_services.payment_id=%s;"""
        query_get_payment_or_tag_name = "select name from payment_services where payment_id=%s"
    elif payment_or_tag_id[-1] == "T":
        query = """
            select 
            * 
            from 
            shops 
            inner join allocated_tags on shops.shop_id = allocated_tags.shop_id 
            where allocated_tags.tag_id=%s;"""
        query_get_payment_or_tag_name = "select name from tags where tag_id=%s"

    #Cookieからユーザーの現在地を取得
    user_latitude = session.get("user_latitude")
    user_longitude = session.get("user_longitude") 

    cur.execute(query, (payment_or_tag_id,))
    shops = cur.fetchall()

    shops_and_payments = []
    for shop_dict in shops:
        distance = location_distance(user_latitude, 
                                    user_longitude, 
                                    shop_dict["latitude"], 
                                    shop_dict["longitude"])
        shop_list = [shop_dict["shop_id"], shop_dict["name"], distance]
        shops_and_payments.append(shop_list)

    # 距離(distance)でソートする
    shops_and_payments.sort(key=lambda x: x[2])

    #見やすいようにkmかmに変換する
    shops_and_payments = list(map(conversion_km_or_m, shops_and_payments)) 

    #タグ名か決済サービス名を取得する
    cur.execute(query_get_payment_or_tag_name, (payment_or_tag_id,))
    searched_strings = cur.fetchall()[0]["name"]
    
    # お店で使用できる決済サービスの名前を追加する
    get_can_use_services(shops_and_payments) 
        
    # カテゴリ欄のデータを取得する
    tag_id_name_list, cash_group, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list = get_category_data()
    
    web_hierarchy_search='検索結果'
    
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
        selected_distance=-1, 
        searched_strings=searched_strings,
        web_hierarchy_search=web_hierarchy_search)
    

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
    select_distance = request.form["select_distance"]

    select_distance = int(select_distance)

    # 距離指定がない場合は-1が返ってくる
    if select_distance == -1:
        distance_limit_sql = ""
        be_all_distance = True
    else:
        be_all_distance = False
        # select_distanceで指定した範囲を指定する
        result = get_distanced_lat_lng(user_latitude, 
                                        user_longitude, 
                                        select_distance)
        n = str(result["n"])
        e = str(result["e"])
        s = str(result["s"])
        w = str(result["w"])

        # 距離を指定するためのsqlを作成しておく
        distance_limit_sql = f""" ({n} > shops.latitude and shops.latitude > {s}) 
                                and ({e} > shops.longitude and shops.longitude > {w}) """

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

    # 距離の検索と文字列検索を兼ねているため、文字列が何も入力されていない場合は距離だけの絞り込みを行う
    if search_strings == '':
        query_to_shops = "select * from shops " 
        query_to_payment_services = "select * from payment_services "
        query_to_tags = "select * from tags "
        query_every_search_word = [[query_to_shops, query_to_payment_services, query_to_tags]]
        variable_every_search_word = [()]
        search_result_shops = execut_sql_search(query_every_search_word, 
                                                variable_every_search_word, 
                                                distance_limit_sql, 
                                                be_all_distance, 
                                                be_input_search_word=False)
    # 検索に使えるwordが無い場合は結果を空にしておく 
    elif len(search_strings_list) == 0:
        search_result_shops = []
    else:
        # 類似語や省略形があれば、検索に適した単語も検索リストに加える
        search_strings_list = search_synonym(search_strings_list)
        # 検索を行うためにsqlを発行する
        query_every_search_word, variable_every_search_word = create_sql_search_n_gram(search_strings_list)
        # 検索を行う
        search_result_shops = execut_sql_search(query_every_search_word, 
                                                variable_every_search_word, 
                                                distance_limit_sql, 
                                                be_all_distance)

        # 検索件数が極端に少ない場合,検索ワードごとにlike句での検索を再び行う
        if len(search_result_shops) <= MIN_NUM_SEARCH_RESULTS:
            like_query_every_search_word, variable_every_search_word = create_sql_search_like(search_words)
            search_result_shops += execut_sql_search(like_query_every_search_word, 
                                                    variable_every_search_word, 
                                                    distance_limit_sql, 
                                                    be_all_distance)

    # 検索結果の重複を削除
    search_result_shops = get_unique_list(search_result_shops)
    
    shops_and_payments = []
    for shop_dict in search_result_shops:
        distance = location_distance(user_latitude, 
                                    user_longitude, 
                                    shop_dict["latitude"], 
                                    shop_dict["longitude"])
        shop_list = [shop_dict["shop_id"], shop_dict["name"], distance]
        shops_and_payments.append(shop_list)
    
    #正確な距離制限を掛ける
    shops_and_payments = accurately_determine_distance(shops_and_payments, select_distance)
    
    # 距離(distance)でソートする
    shops_and_payments.sort(key=lambda x: x[2])

    #見やすいようにkmかmに変換する
    shops_and_payments = list(map(conversion_km_or_m, shops_and_payments)) 
    
    # お店で使用できる決済サービスの名前を追加する
    get_can_use_services(shops_and_payments)

    # カテゴリ欄のデータを取得する
    tag_id_name_list, cash_group, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list = get_category_data()

    # webの階層構造の文字のリスト
    web_hierarchy_search='検索結果'
    
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
        selected_distance=select_distance, 
        searched_strings=search_strings,
        web_hierarchy_search=web_hierarchy_search)

@bp.route('/map-search-result/text-search', methods=['POST'])
def text_search_map():
    db = get_db()
    cur = db.cursor(dictionary=True)

    #Cookieからユーザーの現在地を取得
    user_latitude = session.get("user_latitude")
    user_longitude = session.get("user_longitude") 

    # htmlから検索を掛ける文字列を取得する
    # 半角スペースや全角スペースごとに区切る
    search_strings = request.form["search_strings"]
    search_words = search_strings.split()
    select_distance = request.form["select_distance"]

    select_distance = int(select_distance)

    # 距離指定がない場合は-1が返ってくる
    if select_distance == -1:
        distance_limit_sql = ""
        be_all_distance = True
    else:
        be_all_distance = False
        # select_distanceで指定した範囲を指定する
        result = get_distanced_lat_lng(user_latitude, 
                                        user_longitude, 
                                        select_distance)
        n = str(result["n"])
        e = str(result["e"])
        s = str(result["s"])
        w = str(result["w"])

        # 距離を指定するためのsqlを作成しておく
        distance_limit_sql = f""" ({n} > shops.latitude and shops.latitude > {s}) 
                                and ({e} > shops.longitude and shops.longitude > {w}) """

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

    # 距離の検索と文字列検索を兼ねているため、文字列が何も入力されていない場合は距離だけの絞り込みを行う
    if search_strings == '':
        query_to_shops = "select * from shops " 
        query_to_payment_services = "select * from payment_services "
        query_to_tags = "select * from tags "
        query_every_search_word = [[query_to_shops, query_to_payment_services, query_to_tags]]
        variable_every_search_word = [()]
        search_result_shops = execut_sql_search(query_every_search_word, 
                                                variable_every_search_word, 
                                                distance_limit_sql, 
                                                be_all_distance, 
                                                be_input_search_word=False)
    # 検索に使えるwordが無い場合は結果を空にしておく 
    elif len(search_strings_list) == 0:
        search_result_shops = []
    else:
        # 類似語や省略形があれば、検索に適した単語も検索リストに加える
        search_strings_list = search_synonym(search_strings_list)
        # 検索を行うためにsqlを発行する
        query_every_search_word, variable_every_search_word = create_sql_search_n_gram(search_strings_list)
        # 検索を行う
        search_result_shops = execut_sql_search(query_every_search_word, 
                                                variable_every_search_word, 
                                                distance_limit_sql, 
                                                be_all_distance)

        # 検索件数が極端に少ない場合,検索ワードごとにlike句での検索を再び行う
        if len(search_result_shops) <= MIN_NUM_SEARCH_RESULTS:
            like_query_every_search_word, variable_every_search_word = create_sql_search_like(search_words)
            search_result_shops += execut_sql_search(like_query_every_search_word, 
                                                    variable_every_search_word, 
                                                    distance_limit_sql, 
                                                    be_all_distance)

    # 検索結果の重複を削除
    search_result_shops = get_unique_list(search_result_shops)
    
    shops_and_payments = []
    for shop_dict in search_result_shops:
        distance = location_distance(user_latitude, 
                                        user_longitude, 
                                        shop_dict["latitude"], 
                                        shop_dict["longitude"])
        # お店のid、名前、距離、緯度経度のリストを作る
        shop_list = [shop_dict["shop_id"], shop_dict["name"], distance, shop_dict["latitude"], shop_dict["longitude"]]
        shops_and_payments.append(shop_list)
    
    #正確な距離制限を掛ける
    shops_and_payments = accurately_determine_distance(shops_and_payments, select_distance)
    
    # 距離(distance)でソートする
    shops_and_payments.sort(key=lambda x: x[2])

    #見やすいようにkmかmに変換する
    shops_and_payments = list(map(conversion_km_or_m, shops_and_payments)) 
    
    # お店で使用できる決済サービスの名前を追加する
    get_can_use_services(shops_and_payments)

    # カテゴリ欄のデータを取得する
    tag_id_name_list, cash_group, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list = get_category_data()

    # webの階層構造の文字のリスト
    web_hierarchy_search='検索結果'
    
    # .envに書いてあるAPI keyを読み込む
    api_key = load_api_key()
        
    return render_template(
        "map.html",
        shops_and_payments=shops_and_payments, 
        tag_id_name_list=tag_id_name_list, 
        cash_group=cash_group,
        barcode_names=barcode_names,
        credit_names=credit_names,
        electronic_money_names=electronic_money_names, 
        tag_commonly_used_list=tag_commonly_used_list, 
        DROP_DOWN_DISTANCE=DROP_DOWN_DISTANCE, 
        selected_distance=select_distance, 
        searched_strings=search_strings,
        web_hierarchy_search=web_hierarchy_search,
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        api_key=api_key)

@bp.route('/map-search-result/<string:payment_or_tag_id>')
def search_result_map(payment_or_tag_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # "決済サービス"か"タグ"かを判別する
    if payment_or_tag_id[-1] == "P":
        query = """
            select 
            * 
            from 
            shops 
            inner join can_use_services on shops.shop_id = can_use_services.shop_id 
            where can_use_services.payment_id=%s;"""
        query_get_payment_or_tag_name = "select name from payment_services where payment_id=%s"
    elif payment_or_tag_id[-1] == "T":
        query = """
            select 
            * 
            from 
            shops 
            inner join allocated_tags on shops.shop_id = allocated_tags.shop_id 
            where allocated_tags.tag_id=%s;"""
        query_get_payment_or_tag_name = "select name from tags where tag_id=%s"

    #Cookieからユーザーの現在地を取得
    user_latitude = session.get("user_latitude")
    user_longitude = session.get("user_longitude") 

    cur.execute(query, (payment_or_tag_id,))
    shops = cur.fetchall()

    shops_and_payments = []
    for shop_dict in shops:
        distance = location_distance(user_latitude, 
                                        user_longitude, 
                                        shop_dict["latitude"], 
                                        shop_dict["longitude"])
        # お店のid、名前、距離、緯度経度のリストを作る
        shop_list = [shop_dict["shop_id"], shop_dict["name"], distance, shop_dict["latitude"], shop_dict["longitude"]]
        shops_and_payments.append(shop_list)

    # 距離(distance)でソートする
    shops_and_payments.sort(key=lambda x: x[2])

    #見やすいようにkmかmに変換する
    shops_and_payments = list(map(conversion_km_or_m, shops_and_payments)) 

    #タグ名か決済サービス名を取得する
    cur.execute(query_get_payment_or_tag_name, (payment_or_tag_id,))
    searched_strings = cur.fetchall()[0]["name"]
    
    # お店で使用できる決済サービスの名前を追加する
    get_can_use_services(shops_and_payments) 
        
    # カテゴリ欄のデータを取得する
    tag_id_name_list, cash_group, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list = get_category_data()
    
    web_hierarchy_search='検索結果'
    
    # .envに書いてあるAPI keyを読み込む
    api_key = load_api_key()
    
    return render_template(
        "map.html", 
        shops_and_payments=shops_and_payments, 
        tag_id_name_list=tag_id_name_list, 
        cash_group=cash_group,
        barcode_names=barcode_names, 
        credit_names=credit_names, 
        electronic_money_names=electronic_money_names, 
        tag_commonly_used_list=tag_commonly_used_list, 
        DROP_DOWN_DISTANCE=DROP_DOWN_DISTANCE, 
        selected_distance=-1, 
        searched_strings=searched_strings,
        web_hierarchy_search=web_hierarchy_search,
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        api_key=api_key)
