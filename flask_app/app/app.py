from flask import Flask,render_template
import csv
import os
from flask import request

#Flaskオブジェクトの生成
app = Flask(__name__)

this_dir_path = os.path.dirname(os.path.abspath(__file__))


def get_csv():
    with open(this_dir_path+'/static/shop.csv') as f: #実行しているのがrun.pyなのでカレントディレクトリが一段上になっている.
        reader = csv.reader(f)
        l = [row for row in reader]
    return l


@app.route("/")
def top():
    l = get_csv()
    return render_template("top.html", shops=l)


@app.route("/detail")
def detail():
    l = get_csv()
    req = request.args
    shop_id = int(req.get("shop_id"))
    print(shop_id)
    print(type(shop_id))
    shop_detail = l[shop_id]
    return render_template("detail.html", shop_detail=shop_detail)



if __name__ == "__main__":
    app.run(debug=True)

