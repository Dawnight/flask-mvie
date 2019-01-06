# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, flash, session, request, abort
from . import admin
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Adminlog, Userlog, Auth, Role
from app import db, app
from functools import wraps
from werkzeug.utils import secure_filename
import os, uuid, datetime


# 上下文处理器
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )
    return data


def admin_login_req(f):
    @wraps(f)
    def decorator_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)

    return decorator_function


# 权限控制的装饰器
def admin_auth(f):
    @wraps(f)
    def decorator_function(*args, **kwargs):
        admin = Admin.query.join(Role).filter(Role.id == Admin.role_id, Admin.id == session['admin_id']).first()
        auths = admin.role.auths
        auths = list(map(lambda v: int(v), auths.split(',')))
        auth_list = Auth.query.all()
        rule = request.url_rule
        urls = [v.url for v in auth_list for val in auths if val == v.id]
        # if str(rule) not in urls:
        #     abort(404)
        return f(*args, **kwargs)
    return decorator_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


@admin.route('/')
@admin_login_req
@admin_auth
def index():
    return render_template('admin/index.html')


@admin.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin.check_pwd(data['pwd']):
            flash('密码错误', 'err')
            return redirect(url_for('admin.login'))
        session['admin'] = data['account']
        session['admin_id'] = admin.id
        adminlog = Adminlog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html', form=form)


@admin.route('/logout/')
@admin_login_req
def logout():
    session.pop('account', None)
    session.pop('admin_id', None)
    return redirect(url_for('admin.login'))


@admin.route('/pwd/', methods=['GET', 'POST'])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session['admin']).first()
        from werkzeug.security import generate_password_hash
        # admin.pwd = generate_password_hash(data['new_pwd'])
        admin.pwd = data['new_pwd']
        db.session.add(admin)
        db.session.commit()
        flash('修改密码成功，请重新登录', 'ok')
        return redirect(url_for('admin.logout'))
    return render_template('admin/pwd.html', form=form)


@admin.route('/tag/add/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data['name']).count()
        if tag == 1:
            flash('名称已经存在', 'err')
            return redirect(url_for('admin.tag_add'))
        tag = Tag(
            name=data['name']
        )
        db.session.add(tag)
        db.session.commit()
        flash('添加标签成功', 'ok')
        oplog = Oplog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
            reason='添加标签%s' % data['name']
        )
        db.session.add(oplog)
        db.session.commit()
        redirect(url_for('admin.tag_add'))
    return render_template('admin/tag_add.html', form=form)


@admin.route('/tag/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def tag_list(page=None):
    if page is None:
        page = 1
    page_data = Tag.query.order_by(Tag.id).paginate(page=page, per_page=10)
    return render_template('admin/tag_list.html', page_data=page_data)


@admin.route('/tag/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def tag_del(id=None):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash('删除标签成功', 'ok')
    return redirect(url_for('admin.tag_list', page=1))


@admin.route('/tag/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def tag_edit(id=None):
    form = TagForm()
    form.submit.label.text = "修改"
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data['name']).count()
        if tag.name != data['name'] and tag_count == 1:
            flash('名称已经存在', 'err')
            return redirect(url_for('admin.tag_edit', id=id))
        tag.name = data['name']
        db.session.add(tag)
        db.session.commit()
        flash('修改标签成功', 'ok')
        redirect(url_for('admin.tag_edit', id=id))
    return render_template('admin/tag_edit.html', form=form, tag=tag)


@admin.route('/movie/add', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], 0o770)
        url = change_filename(form.url.data.filename)
        logo = change_filename(form.logo.data.filename)
        form.url.data.save(app.config['UP_DIR'] + url)
        form.logo.data.save(app.config['UP_DIR'] + logo)
        movie = Movie(
            title=data['title'],
            url=url,
            info=data['info'],
            logo=logo,
            star=int(data['star']),
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            release_time=data['release_time'],
            length=data['length'],
        )
        db.session.add(movie)
        db.session.commit()
        flash('电影添加成功', 'ok')
        return redirect(url_for('admin.movie_add'))
    return render_template('admin/movie_add.html', form=form)


@admin.route('/movie/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def movie_list(page=None):
    if page is None:
        page = 1
    page_data = Movie.query.join(Tag).filter(Tag.id == Movie.tag_id).order_by(Tag.id).paginate(page=page, per_page=10)
    return render_template('admin/movie_list.html', page_data=page_data)


# 删除电影
@admin.route('/movie/del/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_del(id=None):
    movie = Movie.query.get_or_404(id)
    db.session.delete(movie)
    db.session.commit()
    flash('删除成功', 'ok')
    return redirect(url_for('admin.movie_list', page=1))


@admin.route('/movie/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.get_or_404(id)
    if request.method == 'GET':
        form.info.data = movie.info
        form.tag_id.data = int(movie.tag_id)
        form.star.data = int(movie.star)
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        if movie_count == 1 and movie.title != data['title']:
            flash('电影名已经存在', 'err')
            return redirect(url_for('admin.movie_edit', id=id))
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], 0o770)
        if form.url.data != "":
            file_url = secure_filename(form.url.data.filename)
            movie.url = change_filename(form.url.data.filename)
            form.url.data.save(app.config["UP_DIR"] + movie.url)
        if form.logo.data != "":
            file_logo = secure_filename(form.logo.data.filename)
            movie.logo = change_filename(form.logo.data.filename)
            form.logo.data.save(app.config["UP_DIR"] + movie.logo)
        movie.star = data["star"]
        movie.tag_id = data["tag_id"]
        movie.info = data["info"]
        movie.title = data["title"]
        movie.area = data["area"]
        movie.length = data["length"]
        movie.release_time = data["release_time"]
        db.session.add(movie)
        db.session.commit()
        flash("修改电影成功！", "ok")
        return redirect(url_for('admin.movie_edit', id=movie.id))
    return render_template('admin/movie_edit.html', form=form, movie=movie)


@admin.route('/preview/add', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], 0o770)
        logo = change_filename(form.logo.data.filename)
        form.logo.data.save(app.config['UP_DIR'] + logo)
        preview = Preview(
            title=data['title'],
            logo=logo,
        )
        db.session.add(preview)
        db.session.commit()
        flash('添加预告片成功', 'ok')
        return redirect(url_for('admin.preview_add'))
    return render_template('admin/preview_add.html', form=form)


@admin.route('/preview/list/<int:page>')
@admin_login_req
@admin_auth
def preview_list(page=None):
    if page is None:
        page = 1
    page_data = Preview.query.order_by(Preview.id).paginate(page=page, per_page=10)
    return render_template('admin/preview_list.html', page_data=page_data)


@admin.route('/preview/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def preview_del(id=None):
    preview = Preview.query.filter_by(id=id).first_or_404()
    db.session.delete(preview)
    db.session.commit()
    flash('删除预告片成功', 'ok')
    return redirect(url_for('admin.preview_list', page=1))


@admin.route('/preview/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_edit(id=None):
    form = PreviewForm()
    form.submit.label.text = "修改"
    form.logo.validators = []
    preview = Preview.query.get_or_404(id)
    if request.method == 'GET':
        form.title.data = preview.title
    if form.validate_on_submit():
        data = form.data
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], 0o770)
        if form.logo.data != "":
            preview.logo = change_filename(form.logo.data.filename)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)
        preview.title = data['title']
        db.session.add(preview)
        db.session.commit()
        flash('修改预告片成功', 'ok')
        redirect(url_for('admin.preview_edit', id=id))
    print(form)
    print(preview)
    return render_template('admin/preview_edit.html', form=form, preview=preview)


@admin.route('/user/view/<int:id>/')
@admin_login_req
@admin_auth
def user_view(id=None):
    user = User.query.get_or_404(id)
    return render_template('admin/user_view.html', user=user)


@admin.route('/user/list/<int:page>/')
@admin_login_req
@admin_auth
def user_list(page):
    if page is None:
        page = 1
    page_data = User.query.order_by(User.id).paginate(page=page, per_page=10)
    return render_template('admin/user_list.html', page_data=page_data)


@admin.route('/user/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def user_del(id=None):
    user = User.query.filter_by(id=id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    flash('删除用户成功', 'ok')
    return redirect(url_for('admin.user_list', page=1))


@admin.route('/comment/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def comment_list(page):
    if page is None:
        page = 1
    page_data = Comment.query.join(Movie) \
        .join(User) \
        .filter(Movie.id == Comment.movie_id, User.id == Comment.user_id) \
        .order_by(Comment.id) \
        .paginate(page=page, per_page=10)
    return render_template('admin/comment_list.html', page_data=page_data)


@admin.route('/comment/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def comment_del(id=None):
    comment = Comment.query.filter_by(id=id).first_or_404()
    db.session.delete(comment)
    db.session.commit()
    flash('删除评论成功', 'ok')
    return redirect(url_for('admin.comment_list', page=1))


@admin.route('/moviecol/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def moviecol_list(page):
    if page is None:
        page = 1
    page_data = Moviecol.query.join(Movie) \
        .join(User) \
        .filter(Movie.id == Moviecol.movie_id, User.id == Moviecol.user_id) \
        .order_by(Moviecol.id) \
        .paginate(page=page, per_page=10)
    return render_template('admin/moviecol_list.html', page_data=page_data)


@admin.route('/moviecol/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def moviecol_del(id=None):
    moviecol = Moviecol.query.filter_by(id=id).first_or_404()
    db.session.delete(moviecol)
    db.session.commit()
    flash('删除收藏成功', 'ok')
    return redirect(url_for('admin.moviecol_list', page=1))


@admin.route('/oplog/list/<int:page>/')
@admin_login_req
@admin_auth
def oplog_list(page):
    if page is None:
        page = 1
    page_data = Oplog.query.join(Admin) \
        .filter(Admin.id == Oplog.admin_id) \
        .order_by(Oplog.id) \
        .paginate(page=page, per_page=10)
    return render_template('admin/oplog_list.html', page_data=page_data)


@admin.route('/adminloginlog/list/<int:page>/')
@admin_login_req
@admin_auth
def adminloginlog_list(page):
    if page is None:
        page = 1
    page_data = Adminlog.query.join(Admin) \
        .filter(Admin.id == Adminlog.admin_id) \
        .order_by(Adminlog.id) \
        .paginate(page=page, per_page=10)
    return render_template('admin/adminloginlog_list.html', page_data=page_data)


@admin.route('/userloginlog/list/<int:page>/')
@admin_login_req
@admin_auth
def userloginlog_list(page):
    if page is None:
        page = 1
    page_data = Userlog.query.join(User) \
        .filter(User.id == Userlog.user_id) \
        .order_by(Userlog.id) \
        .paginate(page=page, per_page=10)
    return render_template('admin/userloginlog.html', page_data=page_data)


@admin.route('/role/add', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        role = Role(
            name=data['name'],
            auths=",".join(map(lambda v: str(v), data['auths'])),
        )
        db.session.add(role)
        db.session.commit()
        flash('添加角色成功', 'ok')
    return render_template('admin/role_add.html', form=form)


@admin.route('/role/list/<int:page>/')
@admin_login_req
@admin_auth
def role_list(page):
    if page is None:
        page = 1
    page_data = Role.query.order_by(Role.id).paginate(page=page, per_page=10)
    return render_template('admin/role_list.html', page_data=page_data)


@admin.route('/role/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def role_edit(id=None):
    form = RoleForm()
    role = Role.query.get_or_404(id)
    if request.method == 'GET':
        form.auths.data = list(map(lambda v: int(v), role.auths.split(',')))
    form.submit.label.text = "修改"
    if form.validate_on_submit():
        data = form.data
        role.name = data['name']
        role.auths = ",".join(map(lambda v: str(v), data["auths"]))
        db.session.add(role)
        db.session.commit()
        flash('修改角色成功', 'ok')
        redirect(url_for('admin.role_edit', id=id))
    return render_template('admin/role_edit.html', form=form, role=role)


@admin.route('/role/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def role_del(id=None):
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash('删除收藏成功', 'ok')
    return redirect(url_for('admin.role_list', page=1))


@admin.route('/auth/add', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data['name'],
            url=data['url']
        )
        db.session.add(auth)
        db.session.commit()
        flash('添加权限成功', 'ok')
    return render_template('admin/auth_add.html', form=form)


@admin.route('/auth/list/<int:page>/')
@admin_login_req
@admin_auth
def auth_list(page):
    if page is None:
        page = 1
    page_data = Auth.query.order_by(Auth.id).paginate(page=page, per_page=10)
    return render_template('admin/auth_list.html', page_data=page_data)


@admin.route('/auth/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def auth_del(id=None):
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash('删除标签成功', 'ok')
    return redirect(url_for('admin.auth_list', page=1))


@admin.route('/auth/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    form.submit.label.text = "修改"
    if form.validate_on_submit():
        data = form.data
        auth.url = data['url']
        auth.name = data['name']
        db.session.add(auth)
        db.session.commit()
        flash('修改权限成功', 'ok')
        redirect(url_for('admin.auth_edit', id=id))
    return render_template('admin/auth_edit.html', form=form, auth=auth)


@admin.route('/admin/add', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def admin_add():
    form = AdminForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data['name'],
            pwd=data['pwd'],
            role_id=data['role_id'],
            is_super=1,
        )
        db.session.add(admin)
        db.session.commit()
        flash('添加管理员成功', 'ok')
    return render_template('admin/admin_add.html', form=form)


@admin.route('/admin/list/<int:page>')
@admin_login_req
@admin_auth
def admin_list(page):
    if page is None:
        page = 1
    page_data = Admin.query.join(Role).filter(Role.id == Admin.role_id).order_by(Admin.id).paginate(page=page,
                                                                                                    per_page=10)
    return render_template('admin/admin_list.html', page_data=page_data)
