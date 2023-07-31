from flask import Blueprint, render_template

index_bp = Blueprint('index', __name__, template_folder='../templates', static_folder='../static')

@index_bp.route('/', methods=['GET', 'POST'])
def front_page():
  return render_template('index.html')