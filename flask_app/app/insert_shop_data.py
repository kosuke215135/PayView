from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from db import get_db
from admin_privacy import login_required

CASH_GROUP = "01PG"
BARCODE_GROUP = "02PG"
CREDIT_GROUP = "03PG"
ELECTRONIC_MONEY_GROUP = "04PG"
TRANSPORTATION_GROUP = "05PG"
DROP_DOWN_PAYMENT_GROUP_LIST = ["02PG","03PG","04PG","05PG"]

bp = Blueprint('insert_shop_data', __name__, url_prefix='/insert-shop-data')


@bp.route('/choose-shop/<string:tag_or_payment>')
@login_required
def choose_shop(tag_or_payment):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("select shop_id,name from shops;")
    shop_id_name_list = cur.fetchall()
    return render_template('insert_shop_data/choose_shop.html', shop_id_name_list=shop_id_name_list, tag_or_payment=tag_or_payment)



def take_out_payment_id(dict_content):
    return dict_content["payment_id"]


@bp.route('/choose-payment/<int:shop_id>', methods=('GET', 'POST'))
@login_required
def choose_payment(shop_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "GET":
        cur.execute("select * from payment_services;")
        payment_id_name_list = cur.fetchall()
        cur.execute(f"SELECT * FROM shops WHERE shop_id={shop_id};")
        shop_data = cur.fetchall()
        
        cur.execute(f"select payment_id from can_use_services where shop_id={shop_id};")
        can_use_pay_this_shop = cur.fetchall()
        can_use_pay_this_shop_list = list(map(take_out_payment_id, can_use_pay_this_shop))
        
        return render_template('insert_shop_data/choose_payment.html', payment_id_name_list=payment_id_name_list, shop_data=shop_data, can_use_pay_this_shop_list=can_use_pay_this_shop_list)

    if request.method == "POST":
        can_use_pay =request.form.getlist("payment")
        cur.execute(f"select payment_id from can_use_services where shop_id={shop_id}")
        now_use_pay = cur.fetchall()
        now_use_pay_list = list(map(take_out_payment_id, now_use_pay))
        for i in can_use_pay:
            if i not in now_use_pay_list:
                cur.execute(f"insert into can_use_services values ({shop_id},'{i}');")
        db.commit()

        query = f"DELETE FROM can_use_services WHERE shop_id={shop_id}" 
        for i in range(len(can_use_pay)):
            query += f" and payment_id!='{can_use_pay[i]}'"
        cur.execute(query)
        db.commit()
    return redirect(url_for("insert_shop_data.choose_shop", tag_or_payment="payment"))



def take_out_tag_id(dict_content):
    return dict_content["tag_id"]


@bp.route('/choose-tag/<int:shop_id>', methods=('GET', 'POST'))
@login_required
def choose_tag(shop_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "GET":
        cur.execute("select * from tags;")
        tag_id_name_list = cur.fetchall()
        cur.execute(f"SELECT * FROM shops WHERE shop_id={shop_id};")
        shop_data = cur.fetchall()
        
        cur.execute(f"select tag_id from allocated_tags where shop_id={shop_id};")
        assigned_tag_this_shop = cur.fetchall()
        assigned_tag_this_shop_list = list(map(take_out_tag_id, assigned_tag_this_shop))
        
        return render_template('insert_shop_data/choose_tag.html', tag_id_name_list=tag_id_name_list, shop_data=shop_data, assigned_tag_this_shop_list=assigned_tag_this_shop_list)

    if request.method == "POST":
        assigned_tag =request.form.getlist("tag")
        cur.execute(f"select tag_id from allocated_tags where shop_id={shop_id}")
        now_assigned_tag = cur.fetchall()
        now_assigned_tag_list = list(map(take_out_tag_id, now_assigned_tag))
        for i in assigned_tag:
            if i not in now_assigned_tag_list:
                cur.execute(f"insert into allocated_tags values ({shop_id},'{i}');")
        db.commit()

        query = f"DELETE FROM allocated_tags WHERE shop_id={shop_id}" 
        for i in range(len(assigned_tag)):
            query += f" and tag_id!='{assigned_tag[i]}'"
        cur.execute(query)
        db.commit()
    return redirect(url_for("insert_shop_data.choose_shop", tag_or_payment="tag"))





@bp.route('/add-shop', methods=('GET', 'POST'))
@login_required
def add_shop():
    error = 0 #dbに挿入できたかどうかをチェックする
    if request.method == "GET":
        return render_template('insert_shop_data/add_shop.html',error=error)
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        shop_name = request.form["shop_name"]
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        try:
            cur.execute(f"insert into shops (name, latitude, longitude) values ('{shop_name}','{latitude}','{longitude}');")
            db.commit()
        except:
            error = 1
            return render_template('insert_shop_data/add_shop.html', error=error) 
        return redirect(url_for("insert_shop_data.add_shop"))


@bp.route('/add-payment', methods=('GET', 'POST'))
@login_required
def add_payment():
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "GET":
        drop_down_payment_group_dict = {}
        for group_id in DROP_DOWN_PAYMENT_GROUP_LIST:
            cur.execute("select * from payment_groups where group_id=%s", (group_id,))
            group_name = cur.fetchall()[0]["group_name"]
            drop_down_payment_group_dict[group_id] = group_name
        return render_template('insert_shop_data/add_payment.html',
                               drop_down_payment_group_dict=drop_down_payment_group_dict)

    if request.method == "POST":
        cur.execute("select MAX(payment_id) from payment_services;")
        max_payment_id = cur.fetchall()[0]["MAX(payment_id)"]
        # payment_servicesにデータが入っていないとNULLが返ってくる.
        if max_payment_id == None:
            max_payment_id = "000P"
        max_payment_id = max_payment_id[:3]
        max_payment_id_int = int(max_payment_id)
        next_payment_id = str(max_payment_id_int + 1)
        if len(next_payment_id) == 1:
            next_payment_id = "00" + next_payment_id
        elif len(next_payment_id) == 2:
            next_payment_id = "0" + next_payment_id
        next_payment_id += "P"

        payment_name = request.form["payment_name"]
        payment_group = request.form["payment_group"]
        try:
            cur.execute("insert into payment_services values (%s, %s, %s);",
                        (next_payment_id, payment_name, payment_group))
            db.commit()
        except:
            flash("値が正しくありません。")
        return redirect(url_for("insert_shop_data.add_payment"))


@bp.route('/delete-shop', methods=('GET', 'POST'))
@login_required
def delete_shop():
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        delete_shop_id_list =request.form.getlist("shop")
        for i in delete_shop_id_list:
            cur.execute(f"DELETE FROM shops where shop_id = {i};")
        db.commit()
    cur.execute("select shop_id,name from shops;")
    shop_id_name_list = cur.fetchall()
    return render_template('insert_shop_data/delete_shop.html', shop_id_name_list=shop_id_name_list)


@bp.route('/delete-payment', methods=('GET', 'POST'))
@login_required
def delete_payment():
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        delete_payment_id_list =request.form.getlist("payment")
        for i in delete_payment_id_list:
            cur.execute(f"DELETE FROM payment_services where payment_id = '{i}';")
        db.commit()
    cur.execute("select payment_id,name from payment_services;")
    payment_id_name_list = cur.fetchall()
    return render_template('insert_shop_data/delete_payment.html', payment_id_name_list=payment_id_name_list)


@bp.route('/add-tag', methods=('GET', 'POST'))
@login_required
def add_tag():
    if request.method == "GET":
        return render_template('insert_shop_data/add_tag.html')
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("select MAX(tag_id) from tags;")
        max_tag_id = cur.fetchall()[0]["MAX(tag_id)"]
        # payment_servicesにデータが入っていないとNULLが返ってくる.
        if max_tag_id == None:
            max_tag_id = "000T"
        max_tag_id = max_tag_id[:3]
        max_tag_id_int = int(max_tag_id)
        next_tag_id = str(max_tag_id_int + 1)
        if len(next_tag_id) == 1:
            next_tag_id = "00" + next_tag_id
        elif len(next_tag_id) == 2:
            next_tag_id = "0" + next_tag_id
        next_tag_id += "T"

        tag_name = request.form["tag_name"]
        yomi = request.form["hiragana"]
        try:
            cur.execute("insert into tags values (%s, %s, %s)",
                        (next_tag_id, tag_name, yomi))
            db.commit()
        except:
            flash("値が正しくありません。")
        return redirect(url_for("insert_shop_data.add_tag"))


@bp.route('/delete-tag', methods=('GET', 'POST'))
@login_required
def delete_tag():
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "POST":
        delete_tag_id_list =request.form.getlist("tag")
        for i in delete_tag_id_list:
            cur.execute(f"DELETE FROM tags where tag_id = '{i}';")
        db.commit()
    cur.execute("select tag_id,name from tags;")
    tag_id_name_list = cur.fetchall()
    return render_template('insert_shop_data/delete_tag.html', tag_id_name_list=tag_id_name_list)




