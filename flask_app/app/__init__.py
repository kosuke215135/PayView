from flask import Flask,render_template
import csv
import os
from flask import request



this_dir_path = os.path.dirname(os.path.abspath(__file__))



def get_csv():
    with open(this_dir_path+'/static/shop.csv') as f:
        reader = csv.reader(f)
        l = [row for row in reader]
    return l

def create_app():
    #Flaskオブジェクトの生成
    app = Flask(__name__)

    @app.route("/")
    def top():
        l = get_csv()
        return render_template("top.html", shops=l)


    @app.route("/detail/<int:shop_id>")
    def detail(shop_id):
        l = get_csv()
        print(shop_id)
        print(type(shop_id))
        shop_detail = l[shop_id]
        return render_template("detail.html", shop_detail=shop_detail)
    return app



