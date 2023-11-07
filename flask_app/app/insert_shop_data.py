from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from app.db import get_db

bp = Blueprint('insert_shop_data', __name__, url_prefix='/insert-shop-data')


@bp.route('/choose-shop')
def choose_shop():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("select shop_id,name from shops;")
    shop_id_name_list = cur.fetchall()
    return render_template('insert_shop_data/choose_shop.html', shop_id_name_list=shop_id_name_list)



@bp.route('/choose-payment/<int:shop_id>', methods=('GET', 'POST'))
def choose_payment(shop_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == "GET":
        cur.execute("select * from payment_services;")
        payment_id_name_list = cur.fetchall()
        cur.execute(f"SELECT * FROM shops WHERE shop_id={shop_id};")
        shop_data = cur.fetchall()
        return render_template('insert_shop_data/choose_payment.html', payment_id_name_list=payment_id_name_list, shop_data=shop_data)
    if request.method == "POST":
        can_use_pay =request.form.getlist("payment")
        print(shop_id)
        print(can_use_pay)
        for i in can_use_pay:
            cur.execute(f"insert into can_use_services values ({shop_id},'{i}');")
        db.commit()
    return redirect(url_for("insert_shop_data.choose_shop"))



@bp.route('/add-shop', methods=('GET', 'POST'))
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
def add_payment():
    error = 0 #dbに挿入できたかどうかをチェックする
    if request.method == "GET":
        return render_template('insert_shop_data/add_payment.html',error=error)
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(dictionary=True)
        try:
            cur.execute("select MAX(payment_id) from payment_services;")
            max_payment_id = cur.fetchall()[0]["MAX(payment_id)"]
        except IndexError:
            max_payment_id = "000P"
        max_payment_id = max_payment_id[:3]
        max_payment_id_int = int(max_payment_id)
        next_payment_id = str(max_payment_id_int + 1)
        if len(next_payment_id) == 1:
            next_payment_id = "00" + next_payment_id
        elif len(next_payment_id) == 2:
            next_payment_id = "0" + next_payment_id
        next_payment_id += "P"
        shop_name = request.form["payment_name"]
        try:
            cur.execute(f"insert into payment_services values ('{next_payment_id}','{shop_name}');")
            db.commit()
        except:
            error = 1
            return render_template('insert_shop_data/add_payment.html', error=error) 
        return redirect(url_for("insert_shop_data.add_payment"))
