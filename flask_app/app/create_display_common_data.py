from db import get_db

COMMONLY_TAG = ['スーパー', '食堂', '居酒屋', 'ラーメン', 'カフェ']

BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"

# すべての決済サービスの名前を取得する
def get_payment_service_names(group_id):
    db = get_db()
    cur = db.cursor(dictionary=True) 
    cur.execute("""
        SELECT name
        FROM payment_services
        WHERE payment_group = %s
    """, (group_id,))
    return [item["name"] for item in cur.fetchall()]

# すべてのタグの情報を取得する
def get_all_tag():
    db = get_db()
    cur = db.cursor(dictionary=True)
    tag_query = "select * from tags;"
    cur.execute(tag_query)
    tag_id_name_list = cur.fetchall()
    return tag_id_name_list


# top画面とdetail画面で表示されるカテゴリ欄のデータを取得する関数
def get_category_data():
    barcode_names = get_payment_service_names(BARCODE_GROUP)
    credit_names = get_payment_service_names(CREDIT_GROUP)
    electronic_money_names = get_payment_service_names(ELECTRONIC_MONEY_GROUP)

    tag_id_name_list = get_all_tag()

    tag_commonly_used_list = []
    for tag_id_name in tag_id_name_list:
        if tag_id_name['name'] in COMMONLY_TAG:
            tag_id_name_list.remove(tag_id_name)
            tag_commonly_used_list.append(tag_id_name)
    
    return tag_id_name_list, barcode_names, credit_names, electronic_money_names, tag_commonly_used_list

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
        shops_and_payments[i].append(payments_str)