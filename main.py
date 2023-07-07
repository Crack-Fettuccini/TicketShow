from Blueprints.Index.Index import index_bp
from Blueprints.Admin.Admin import admin_bp
from Blueprints.Login.Login import login_bp
from Blueprints.User.User import user_bp
from Blueprints import app

app.register_blueprint(index_bp, url_prefix=  "/")
app.register_blueprint(login_bp, url_prefix=  "/Login")
app.register_blueprint(user_bp, url_prefix=  "/User")
app.register_blueprint(admin_bp, url_prefix=  "/Admin")

if __name__ == '__main__':
  app.debug = True
  app.run(host='0.0.0.0', port=81)

