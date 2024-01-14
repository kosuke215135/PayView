from db import get_db

COMMONLY_TAG = ['スーパー', '食堂', '居酒屋', 'ラーメン', 'カフェ']

CASH_GROUP = "01PG"
BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"

ADAN_HIRAGANA_LIST = ['あ', 'か', 'さ', 'た', 'な','は', 'ま', 'や', 'ら', 'わ' ]

# 指定した種類の決済サービスの名前とidを取得する
def get_payment_service_ids_names(group_id):
    db = get_db()
    cur = db.cursor(dictionary=True) 
    cur.execute("""
        SELECT 
        payment_id, 
        name
        FROM 
        payment_services
        WHERE 
        payment_group = %s
    """, (group_id,))

    payments = cur.fetchall()

    return payments

# すべてのタグの情報を取得する
def get_all_tag():
    db = get_db()
    cur = db.cursor(dictionary=True)
    # 読みで昇順に並び替えて取得
    tag_query = "select * from tags order by pronunciation ASC;"
    cur.execute(tag_query)
    tag_id_name_list = cur.fetchall()
    return tag_id_name_list


def sort_tags_japanese_alphabetical_order(tag_id_name_list):
    """
    Args:
        tag_id_name_list [{str}]: tagの情報を格納しているリスト
    
    Returns:
        {[{str: x}]}: 50音順に並び替えて、行ごとに分けてdict(デフォルトで順序付き辞書)に格納する
    """
    return_dict = {}
    for i in range(len(ADAN_HIRAGANA_LIST)):
        search_gyou_askii = ord(ADAN_HIRAGANA_LIST[i])
        try:
            next_gyou_askii = ord(ADAN_HIRAGANA_LIST[i+1])
        except:
            #ダミーの数字を入れておく(ひらがなのASKIIコードは12353~12435)
            next_gyou_askii = 100000
        tmp_list = []
        for tag in tag_id_name_list:
            hira = tag["pronunciation"]
            first_hira = hira[0]
            first_hira_askii = ord(first_hira) 
            if search_gyou_askii <= first_hira_askii and first_hira_askii < next_gyou_askii:
                tmp_list.append(tag)
        if len(tmp_list) != 0:
            return_dict[ADAN_HIRAGANA_LIST[i]] = tmp_list
    
    return return_dict
        



# top画面とdetail画面で表示されるカテゴリ欄のデータを取得する関数
def get_category_data():
    cash_group = get_payment_service_ids_names(CASH_GROUP)
    barcode_names = get_payment_service_ids_names(BARCODE_GROUP)
    credit_names = get_payment_service_ids_names(CREDIT_GROUP)
    electronic_money_names = get_payment_service_ids_names(ELECTRONIC_MONEY_GROUP)

    tag_id_name_list = get_all_tag()

    tag_commonly_used_list = []
    for tag_id_name in tag_id_name_list:
        if tag_id_name['name'] in COMMONLY_TAG:
            tag_id_name_list.remove(tag_id_name)
            tag_commonly_used_list.append(tag_id_name)
    
    tag_id_name_dict_every_gyou = sort_tags_japanese_alphabetical_order(tag_id_name_list) 
    
    return tag_id_name_dict_every_gyou, cash_group, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list

# top画面で決済サービスの一部を表示させるための関数
# 引数で受け取った店の情報が入ったリストに決済サービスの名前も追加する
def get_can_use_services(shops_and_payments):
    db = get_db()
    cur = db.cursor(dictionary=True)
    for i in range(len(shops_and_payments)):
        shop_id = shops_and_payments[i][0]
        join_query = """
            select 
            payment_services.name 
            from can_use_services 
            inner join 
            payment_services 
            on can_use_services.payment_id = payment_services.payment_id 
            where can_use_services.shop_id = %s
        """
        cur.execute(join_query, (shop_id,))
        payments_name_list = cur.fetchall() 
        payments_str = ""
        for l in range(len(payments_name_list)):
            if l == len(payments_name_list)-1:
                payments_str = payments_str + payments_name_list[l]["name"]
                continue
            payments_str = payments_str + payments_name_list[l]["name"] + ", "
        if (len(payments_str) > 100):
            payments_str = payments_str[:100] + "etc..."
        shops_and_payments[i].append(payments_str)