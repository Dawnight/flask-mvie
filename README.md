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

# 4. 前台布局搭建
+ 静态文件引入: {{ url_for('static', filename='文件路径') }}
+ 定义路由: {{ url_for('模板名.视图名', 变量=参数) }}
+ 定义数据块: {% block 数据块名称 %} {% endblock %}

# 5. 会员页面
+ 登录
```python
@home.route('/login/')
def login():
    return render_template('home/login.html')
```
+ 退出
```python
@home.route('/logout/')
def logout():
    return redirect(url_for('home.login'))
```
+ 会员中心`@home.route('/user/')`
+ 修改密码`@home.route('/pwd/')`
+ 评论记录`@home.route('/comments/')`
+ 登录日志`@home.route('/loginlog/')`
+ 收藏电影`@home.route('/moviecol/')`
+ 搜索页面`@home.route('/search/')`
+ 详情页面`@home.route('/play/')`
+ 404页面
```python
@app.errorhandler(404)
def page_not_found(error):
    return render_template('common/404.html'), 404
```

# 6. 管理员登录
+ `app/__init__.py`中创建db对象
+ `app/models.py`中导入db对象
+ `app/admin/forms.py`中定义表单验证
+ `app/templates/admin/login.html`使用表单字段，信息验证，消息闪现
+ `app/admin/views.py`中处理登录请求，保存会话
+ `app/admin/views.py`中处理登录装饰器，访问控制
