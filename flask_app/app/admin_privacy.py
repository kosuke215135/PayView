import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

bp = Blueprint('admin_auth', __name__, url_prefix='/admin-auth')

@bp.route('/admin_login', methods=('GET', 'POST'))
def admin_login():
    if request.method == 'POST':
        admin_name = request.form['admin_name']
        password = request.form['password']
        db = get_db()
        cur = db.cursor(dictionary=True)
        error = None
        cur.execute('SELECT * FROM admin_certification WHERE admin_name = %s', (admin_name,))
        admin = cur.fetchall()[0]

        if admin is None:
            error = 'Incorrect admin name.'
        elif not check_password_hash(admin['admin_password'], password):
            error = 'Incorrect password.'

        if error is None:
            session['admin_id'] = admin['id']
            return redirect(url_for('insert_shop_data.choose_shop', tag_or_payment="tag"))

        flash(error)

    return render_template('insert_shop_data/admin_login.html')


# @bp.before_app_request
# def load_logged_in_admin():
#     admin_id = session.get('admin_id')
#     db = get_db()
#     cur = db.cursor(dictionary=True)

#     if admin_id is None:
#         g.admin = None
#     else:
#         cur.execute('SELECT * FROM admin WHERE id = %s', (admin_id,))
#         g.admin = cur.fetchall()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'admin_id' not in session:
           return redirect(url_for('admin_auth.admin_login')) 

        return view(**kwargs)

    return wrapped_view