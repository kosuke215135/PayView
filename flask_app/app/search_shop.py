from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from db import get_db

bp = Blueprint('search_shop', __name__, url_prefix='/search-shop')

