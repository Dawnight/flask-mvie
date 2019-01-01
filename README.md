# flask-movie

# 2. blueprint蓝图
+ 蓝图: 一个应用中或跨应用制作应用组件和支持通用的模式
## 2.1 作用
+ 将不同的功能模块化
+ 构建大型应用
+ 优化项目结构
+ 增强可读性，易于维护
## 2.2 蓝图构建项目目录
+ 定义蓝图(`app/admin/__init__.py`)
```python
from flask import Blueprint
admin = Blueprint('admin', __name__)
import views
```
+ 注册蓝图(`app/__init__.py`)
```python
from admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint, url_prefix='/admin')
```
+ 调用蓝图(`app/admin/views.py`)
```python
from . import admin
@admin.route('/')
```

# 3. 登录日志数据模型设计
+ 安装数据库连接依赖包`pip install flask-sqlalchemy`
+ 定义mysql数据库连接
```python
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URL'] = 'mysql://root:123456@localhost/flask_movie'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
```
+ 定义数据模型
```python
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    pwd = db.Column(db.String)
    email = db.Column(db.String)
    phone = db.Column(db.String)
    info = db.Column(db.Text)
    face = db.Column(db.String)
    addtime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    uuid = db.Column(db.String)
```
