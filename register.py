# encoding='utf-8'
# 导入所需模块
import json
import os
import random
import time
from flask import Flask, render_template, redirect, url_for, flash, abort, session, request, jsonify, \
    send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from wtforms import IntegerField, StringField, SubmitField, HiddenField,PasswordField, IntegerField,ValidationError, RadioField,TextAreaField,DateField
from wtforms.validators import Email, DataRequired, Length, EqualTo,InputRequired, NumberRange

from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from datetime import datetime,date
from flask_cors import CORS

date = DateField("作业日期", format='%Y-%m-%d')

# 创建应用实例
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False # jsonify转变格式的时候不会转变为

#unicode编码格式，unicode编码格式无法直接看到汉字
app.config['JSONIFY_MIMETYPE'] = "application/json;charset=utf-8" # 指定

#浏览器渲染的文件类型，和解码格式
CORS(app, resources=r'/*')
# 配置表单密令
app.secret_key = '\xfe{\xa9\n\x1b0\x16\xcfF\xb103\x9d)\xdf\xfd\xab\xd8\x9b\xbf\xf2\xf5\xb0\x86'
#from some_function import get_img
# 数据库配置
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')  # 数据库URI
SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 更改自动提交
SQLALCHEMY_TRACK_MODIFICATIONS = True


# 相关文件存储地址
UPLOAD_PATH = './static/img/'

# 应用配置
app.config.from_object(__name__)

# 实例化所需模块
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

#数据库

# 登录账号管理

class User(db.Model):
    #设置表数据的类型和表名字
    __tablename__ = 'users'
    #用户id
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(64))
    # 身份
    role = db.Column(db.String(10), default='学生')
    # 冻结状态
    frozen = db.Column(db.Boolean, default=False)
    stu = db.relationship('Student', backref='user', lazy="dynamic")
    tea = db.relationship('Teacher', backref='user', lazy="dynamic")



# 信息管理

# 老师模型创建
class Teacher(db.Model):
    #设置表数据的类型和表名字
    __tablename__ = 'teacher'
    #用户id
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    load_id = db.Column(db.Integer,db.ForeignKey("users.id"))
    #homework = db.relationship('HomeWork', backref='teacher', lazy="dynamic")
    classes = db.relationship('Class', backref='teacher', lazy="dynamic")
    #student = db.relationship('Student', backref='teacher', lazy="dynamic")

    #tea_password = db.Column(db.String(64))
    # 所管理的学生
    # dynamic 表示动态加载 user -> 多个Watermeter
    # student = db.relationship('Student', backref='teacher', lazy='dynamic')
    # 冻结状态
    #frozen = db.Column(db.Boolean, default=False)


# 学生模型
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True,index=True)
    name = db.Column(db.String(64), index=True, unique=True)
    load_id = db.Column(db.Integer,db.ForeignKey("users.id"))
    classes = db.relationship('Class2Student', backref='student', lazy="dynamic")

    #stu_password = db.Column(db.String(64))
    # 所管理的学生
    # dynamic 表示动态加载 user -> 多个Watermeter
    # classes = db.relationship('Class', backref='student', lazy='dynamic')
    # 冻结状态
    #frozen = db.Column(db.Boolean, default=False)

class Teacher2Student(db.Model):
    # teacher_rel = db.Column(db.Integer,db.ForeignKey('teacher.load_id'), primary_key=True)
    # student_rel = db.Column(db.Integer, db.ForeignKey('student.load_id'),primary_key=True)
    teacher_rel = db.Column(db.Integer, primary_key=True)
    student_rel = db.Column(db.Integer, primary_key=True)

# 老师发布作业数据库
class HomeWork(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer,primary_key = True)
    tea_id = db.Column(db.Integer)
    title = db.Column(db.String(64),nullable=False)
    description = db.Column(db.String(255),nullable=False)
    sources = db.Column(db.String(255),nullable=False)
    date = db.Column(db.Date)
    number = db.Column(db.Integer)

# 学生与作业之间的关系
class Student2Homework(db.Model):
    __tablename__ = 'student2homework'


    tea_id = db.Column(db.Integer,primary_key=True)
    stu_id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(64), nullable=False,primary_key=True)
    state = db.Column(db.Boolean, default=False)
    date = db.Column(db.Date)
    score = db.Column(db.Integer,default = 0)
    file = db.Column(db.String(255),default = '')
    description = db.Column(db.String(255),default = '')
# 课程模型
class Class(db.Model):
    __tablename__ = 'class'
    id = db.Column(db.Integer, primary_key=True,index=True)
    tea_id = db.Column(db.Integer,db.ForeignKey("teacher.load_id"))
    name = db.Column(db.String(64), index=True, unique=True,nullable=False)
    time = db.Column(db.String(64))



# 学生选课
class Class2Student(db.Model):
    __tablename__ = 'class2student'

    class_id = db.Column(db.Integer, db.ForeignKey('class.id'),primary_key =True)
    student_id = db.Column(db.Integer,db.ForeignKey('student.load_id'),primary_key =True)
    class_name = db.Column(db.String(64),nullable=False)
    class_time = db.Column(db.String(64),nullable=False)


class File(db.Model):
    #设置表数据的类型和表名字
    __tablename__ = 'file'
    tea_id = db.Column(db.Integer,primary_key = True)
    title = db.Column(db.String(64), nullable=False,primary_key = True)
    description = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date,nullable=False)
    url = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False,primary_key = True)



# 初始化数据库
db.create_all()

# 创建表单——用于 数据库和可视化界面的交互

# 管理员表单模型
class AdminForm(FlaskForm):
    # id验证
    def account_check(self, field):
        if field.data != 'admin':
            raise ValidationError('管理员ID错误')

    # 密码验证
    def password_check(self, field):
        if field.data != 'admincqu':
            raise ValidationError('管理员密码错误')

    admin_id = StringField("管理员ID", validators=[DataRequired(message='请输入ID'), account_check])
    password = PasswordField("管理员密码", validators=[DataRequired(message='请输入密码'), password_check])
    login = SubmitField("管理员登录")


# 用户登录表单模型
class LoginForm(FlaskForm):
    # 验证用户是否存在
    def name_exist(self, field):
        if not User.query.filter_by(name=field.data).first():
            raise ValidationError('用户名不存在')
    name = StringField("用户名", validators=[DataRequired(message='请输入用户名'), name_exist])
    password = PasswordField("密码", validators=[DataRequired(message='请输入密码')])
    login = SubmitField("登录")

# 管理员增加用户表单模型
class AdminAddForm(FlaskForm):
    # 检测用户名唯一性
    def name_unique(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('用户名存在')
    name = StringField('用户名', validators=[DataRequired(), name_unique])
    password = StringField('用户密码', validators=[DataRequired()])
    role = RadioField('身份', choices=[('老师','老师'), ('学生', '学生')], default='学生')
    add = SubmitField("增加用户")

# 获取作业表单
class HomeForm(FlaskForm):
    title =StringField("作业标题")
    description =TextAreaField("作业描述",render_kw={"rows": 5})
    photo = FileField('上传doc或docx格式文件', validators=[FileRequired(), FileAllowed(['doc', 'docx'], '格式错误')])
    date = DateField("截止日期", format='%Y-%m-%d')
    upload = SubmitField('发布')
    state = db.Column(db.Boolean, default=False)


# 提交作业表单
class SubmitForm(FlaskForm):
    description =TextAreaField("作业描述",render_kw={"rows": 5})
    photo = FileField('上传doc或docx格式文件', validators=[FileRequired(), FileAllowed(['doc', 'docx'], '格式错误')])
    upload = SubmitField('提交')



# 老师评分表单

# 登录路由控制
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        # 验证是否被冻结
        if user.frozen:
            flash("你的账户已被冻结")
            return redirect(url_for('login'))
        # 验证密码是否正确
        elif user.password != form.password.data:
            flash("密码不正确")
            return redirect(url_for('login'))
        # 记住登录状态
        session['user_id'] = user.id
        # 根据身份重定向
        if user.role == '学生':
            return redirect('/s/' + str(user.id))
        if user.role == '老师':
            return redirect('/t/' + str(user.id))
    return render_template('login.html', form=form)

# 退出路由控制
@app.route('/logout')
def logout():
    # 管理员退出
    if session.get('admin'):
        session['admin'] = None
    # 普通用户退出
    elif session.get('user_id') is None:
        flash("未登录")
        return redirect(url_for('login'))
    flash("退出成功")
    session['user_id'] = None
    return redirect(url_for('login'))

# 管理员登录路由控制
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    form = AdminForm()
    if form.validate_on_submit():
        session['admin'] = True
        return redirect('/admin/control')
    return render_template('form.html', form=form)

# 管理员控制台路由控制
@app.route('/admin/control', methods=['GET', 'POST'])
def control():
    if not session.get('admin'):
        abort(400)
    try:
        users = User.query.all()
    except:
        users = []
    return render_template('control.html', users=users)


# 管理员新增用户路由控制
@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if not session.get('admin'):
        abort(401,"你无权登录此页面")
    form = AdminAddForm()
    if form.validate_on_submit():
        # 构建用户
        user = User(name=form.name.data, password=form.password.data,
                    role=form.role.data)
        db.session.add(user)
        get_id = (User.query.filter_by(name=form.name.data).first()).id
        if form.role.data == "老师":
            teacher = Teacher(name=form.name.data,load_id = get_id)
            db.session.add(teacher)
            db.session.commit()
        elif form.role.data == "学生":
            student = Student(name=form.name.data, load_id = get_id)
            db.session.add(student)
        flash('增加成功')
        return redirect(url_for('admin_add'))
    return render_template('adminadd.html', form=form)

# 管理员删除用户路由控制
@app.route('/admin/delete', methods=['POST'])
def admin_delete():
    if session.get('admin'):
        user = User.query.filter_by(id=request.form.get('id')).first()
        if user:
            db.session.delete(user)
        return 'ok'
    abort(400)


# 管理员冻结用户路由控制
@app.route('/admin/frozen', methods=['POST'])
def admin_frozen():
    if session.get('admin'):
        user = User.query.filter_by(id=request.form.get('id')).first()
        if user:
            user.frozen = True
            db.session.add(user)
            db.session.commit()
        return '已冻结'
    abort(400)


# 管理员解冻用户路由控制
@app.route('/admin/normal', methods=['POST'])
def admin_normal():
    if session.get('admin'):
        user = User.query.filter_by(id=request.form.get('id')).first()
        user.frozen = False
        db.session.add(user)
        db.session.commit()

        return '已解冻'
    abort(400)

# 老师登录页面
@app.route('/t/<int:id>',methods=["GET","POST"])
def user_teacher(id):
    # 验证是否已登录
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    # 验证身份
    if user.role != '老师':
        abort(400);
    return render_template('both_home.html',form='t', user=user,act=0)

# 学生登录页面
@app.route('/s/<int:id>',methods=["GET","POST"])
def user_student(id):
    # 验证是否已登录
    if session.get('user_id') is None or id != session.get('user_id'):
        session['user_id'] = None
        flash("未登录")
        return redirect(url_for('login'))
    user = User.query.filter_by(id=id).first()
    # 验证身份
    if user.role != '学生':
        abort(400);
    return render_template('both_home.html',form= 's', user=user)

"""
老师端部分
- 课程管理
- 资源集中
    - 上传资源
- 作业管理
    - 发布作业
    - 具体作业
- 实验管理
- 实训平台
"""

## 老师全部页面
# 课程管理
@app.route('/<int:id>/t/classes', methods=['POST',"GET"])
def teacher_page1(id):
    user = User.query.filter_by(id=id).first()
    return render_template('classes.html',form ='t',user= user)

# 资源集中
@app.route('/<int:id>/t/sources', methods=['POST',"GET"])
def teacher_page2(id):
    user = User.query.filter_by(id=id).first()
    homework = HomeWork.query.filter_by(tea_id=id).all()

    if request.method == 'POST':
        resource_name = request.form['resource_name']
        resource_type = request.form['resource_type']
        resource_description = request.form['resource_description']
        file = request.files.get('file')
        basePath = './static/' + "t/" + str(id) + '/'
        filepath = basePath + file.filename
        current_date = datetime.now().date()
        file.save(filepath)
        with db.session.no_autoflush:
            new_data = File(tea_id=id, title=resource_name, \
                            description=resource_description,
                            type=resource_type, \
                            date=current_date, url=filepath)
            db.session.add(new_data)
    file = File.query.filter_by(tea_id=id).all()
    return render_template('sources.html',form='t',user=user,file=file,homework= homework)

@app.route('/<int:id>/t/query_file', methods=['POST'])
def query_file(id):
    user = User.query.filter_by(id=id).first()
    if request.method == 'POST':
        file_type = request.form.get('file_type')
        doc_type = request.form.get('doc_type')
        print(file_type, doc_type)
        if file_type != '' or doc_type != '':
            if file_type == '':
                files = File.query.filter_by(tea_id=id, type=doc_type).all()
            elif doc_type == '':
                files = File.query.filter_by(tea_id=id).all()
            else:
                files = File.query.filter_by(tea_id=id, type=doc_type).all()
            file = []
            for i in files:
                url = i.url
                i_type = (url.split('.'))[-1]
                print(i_type)
                if file_type == 'word':
                    if i_type == 'doc' or i_type == 'docx':
                        file.append(i)
                elif file_type == 'image':
                    if i_type == 'jpg' or i_type == 'png':
                        file.append(i)
                elif i_type == file_type:
                    file.append(i)
            if doc_type == "课程作业":
                homework = HomeWork.query.filter_by(tea_id=id).all()
            else:
                homework = []
        else:
            homework = HomeWork.query.filter_by(tea_id=id).all()
            user = User.query.filter_by(id=id).first()
            file = File.query.filter_by(tea_id=id).all()

    return render_template('sources.html',form='t', file=file,user= user,homework=homework)

@app.route('/<int:id>/t/search', methods=['POST'])
def tea_search(id):
    user = User.query.filter_by(id=id).first()

    if request.method == 'POST':
        search = request.form.get('search')
        print(search)
        if search!='':
            file = File.query.filter(
                db.and_(
                    File.tea_id == id,
                    File.title.ilike(f'%{search}%')
                )
            ).all()
            homework = HomeWork.query.filter(
                db.and_(
                    HomeWork.tea_id == id,
                    HomeWork.title.ilike(f'%{search}%')
                )
            ).all()
        else:
            homework = HomeWork.query.filter_by(tea_id=id).all()
            file = File.query.filter_by(tea_id=id).all()

    return render_template('sources.html', form='t', file=file, user=user, homework=homework)


# 作业管理
@app.route('/<int:id>/t/homework', methods=['POST',"GET"])
def teacher_page3(id):
    user = User.query.filter_by(id=id).first()
    homework = HomeWork.query.filter_by(tea_id=id).all()
    return render_template('homework.html',form='t',user= user,homework=homework)

# 发布作业
@app.route('/<int:id>/t/homeWork', methods=['GET',"POST"])
def homeWork(id):
    user = User.query.filter_by(id=id).first()
    form = HomeForm()
    if form.validate_on_submit():
        flash("作业发布成功！")
        print("ok")
        file = request.files['photo']
        basePath = './static/' + "t/" + str(id) + '/'
        filepath = basePath + file.filename
        if not os.path.exists(basePath):
            os.makedirs(basePath)
        file.save(filepath)
        new_data = HomeWork(tea_id=id,title = form.title.data,\
                            description = form.description.data,\
                            date=form.date.data,sources = filepath,\
                            number=0)
        db.session.add(new_data)
        # Student_get_homework
        tea_stu = Teacher2Student.query.filter_by(teacher_rel = id).all()
        for stu in tea_stu:
            stu_id = stu.student_rel
            home_data= Student2Homework(tea_id = id, stu_id=stu_id,\
                                        state = False,score=0,date=form.date.data,\
                                        title =form.title.data,file = '',\
                                        description = '')
            db.session.add(home_data)

    return render_template('发布作业.html',user=user,form=form)



# 具体作业详情
@app.route('/<int:id>/t/shw/<string:title>', methods=['GET',"POST"])
def shw_teacher(id,title):
    user = User.query.filter_by(id=id).first()
    data = HomeWork.query.filter_by(title=title).first()
    return render_template('shw.html',user = user,form='t',data = data)

# 老师查看学生作业细节
@app.route('/<int:id>/t/<string:title>/detail', methods=['GET', 'POST'])
def detail_student_homework(id, title):
    user = User.query.filter_by(id=id).first()
    # 查询所有学生提交的作业信息

    result = db.session.query(Student.name, Student2Homework.stu_id, Student2Homework.state, Student2Homework.file, Student2Homework.score) \
        .join(Teacher2Student, Teacher2Student.student_rel == Student.id) \
        .join(Student2Homework, (Student.id == Student2Homework.stu_id) & (Student2Homework.title == title)) \
        .filter(Teacher2Student.teacher_rel == id) \
        .all()
    if request.method == 'POST':
        # 获取所有学生的评分
        scores = request.form.getlist('score')
        flash("评分成功")
        # 更新学生的评分
        for i, r in enumerate(result):
            Student2Homework.query.filter_by(stu_id=r.stu_id, title=title).update({Student2Homework.score: scores[i]})
            db.session.commit()
    # 渲染模板
    return render_template('detail_homework.html',user=user, students=result, title=title)

@app.route('/<int:id>/t/<string:title>/detail/<int:stuId>', methods=['GET', 'POST'])
def teacher2student_detail(id,title,stuId):
    user = User.query.filter_by(id=id).first()
    homework = Student2Homework.query.filter_by(title=title,stu_id=stuId).first()
    return render_template("detail_student.html",user = user,title=title,homework = homework)

# 更新得分
# @app.route('/save_score', methods=['POST'])
# def save_score():
#     title = request.form.get('title')
#     stu_id = request.form.get('stu_id')
#     score = request.form.get('score')
#     # 根据title和stu_id查找对应的Student2Homework对象
#     student_homework = Student2Homework.query.filter_by(title=title, stu_id=stu_id).first()
#
#     # 更新学生的分数信息
#     student_homework.score = score
#     db.session.commit()
#
#     flash('评分成功')
#     return redirect(url_for('detail_student_homework', id=student_homework.tea_id, title=title))

# 实验管理
@app.route('/<int:id>/t/experiment', methods=['POST',"GET"])
def teacher_page4(id):

    user = User.query.filter_by(id=id).first()

    return render_template('experiment.html',form = 't',user=user)

# 实训平台
@app.route('/<int:id>/t/train', methods=['POST',"GET"])
def teacher_page5(id):
    user = User.query.filter_by(id=id).first()
    return render_template('train.html',form = 't',user= user)

"""
学生端部分
- 课程管理
- 资源集中
- 作业管理
    - 具体作业
- 实验管理
- 实训平台
"""
## 学生登录全部页面
# 课程管理
@app.route('/<int:id>/s/classes', methods=['POST',"GET"])
def student_page1(id):
    user = User.query.filter_by(id=id).first()
    # tea2stu = Teacher2Student.query.filter_by(student_rel=id).first()
    # tea_id = tea2stu.teacher_rel
    # file = File.query.filter_by(tea_id=tea_id).all()
    return render_template('classes.html',form = 's', act=1,user = user)

# 资源集中
@app.route('/<int:id>/s/sources', methods=['POST',"GET"])
def student_page2(id):
    homework = Student2Homework.query.filter_by(stu_id = id).all()
    user = User.query.filter_by(id=id).first()
    tea2stu = Teacher2Student.query.filter_by(student_rel=id).first()
    tea_id = tea2stu.teacher_rel
    file = File.query.filter_by(tea_id=tea_id).all()
    return render_template('sources.html',form = 's', act=2,user = user,homework=homework,file = file)

@app.route('/<int:id>/s/query_file', methods=['POST'])
def stu_query_file(id):
    user = User.query.filter_by(id=id).first()
    tea2stu = Teacher2Student.query.filter_by(student_rel=id).first()
    tea_id = tea2stu.teacher_rel
    if request.method == 'POST':
        file_type = request.form.get('file_type')
        doc_type = request.form.get('doc_type')
        print(file_type,doc_type)
        if file_type!='' or doc_type!='':
            if file_type=='':
                files = File.query.filter_by(tea_id =tea_id, type=doc_type).all()
            elif doc_type=='':
                files = File.query.filter_by(tea_id =tea_id).all()
            else:
                files = File.query.filter_by(tea_id =tea_id, type=doc_type).all()
            file = []
            for i in files:
                url= i.url
                i_type = (url.split('.'))[-1]
                print(i_type)
                if file_type =='word':
                    if i_type =='doc' or i_type=='docx':
                        file.append(i)
                elif file_type =='image':
                    if i_type =='jpg' or i_type=='png':
                        file.append(i)
                elif i_type==file_type:
                        file.append(i)
            if doc_type == "课程作业":
                homework = Student2Homework.query.filter_by(stu_id=id).all()
            else:
                homework=[]
        else:
            homework = Student2Homework.query.filter_by(stu_id=id).all()
            user = User.query.filter_by(id=id).first()
            tea2stu = Teacher2Student.query.filter_by(student_rel=id).first()
            tea_id = tea2stu.teacher_rel
            file = File.query.filter_by(tea_id=tea_id).all()
            return render_template('sources.html', form='s', file=file, user=user, homework=homework)

    return render_template('sources.html',form='s', file=file,user= user,homework=homework)


@app.route('/<int:id>/s/search', methods=['POST'])
def stu_search(id):
    user = User.query.filter_by(id=id).first()
    tea2stu = Teacher2Student.query.filter_by(student_rel=id).first()
    tea_id = tea2stu.teacher_rel
    if request.method == 'POST':
        search = request.form.get('search')
        print(search)
        if search!='':
            file = File.query.filter(
                db.and_(
                    File.tea_id == tea_id,
                    File.title.ilike(f'%{search}%')
                )
            ).all()
            homework = Student2Homework.query.filter(
                db.and_(
                    Student2Homework.stu_id == id,
                    Student2Homework.title.ilike(f'%{search}%')
                )
            ).all()
        else:
            homework = Student2Homework.query.filter_by(stu_id=id).all()
            user = User.query.filter_by(id=id).first()
            tea2stu = Teacher2Student.query.filter_by(student_rel=id).first()
            tea_id = tea2stu.teacher_rel
            file = File.query.filter_by(tea_id=tea_id).all()

    return render_template('sources.html', form='s', file=file, user=user, homework=homework)


# 作业管理
@app.route('/<int:id>/s/homework', methods=['POST',"GET"])
def student_page3(id):
    user = User.query.filter_by(id=id).first()
    tea2stu = Teacher2Student.query.filter_by(student_rel=id).first()
    #homework = HomeWork.query.filter_by(tea_id=tea2stu.teacher_rel).all()
    homework = Student2Homework.query.filter_by(stu_id = id).all()
    return render_template('homework.html',form='s', act=3,user= user,homework=homework)

# 学生端具体作业查看
@app.route('/<int:id>/s/shw/<string:title>', methods=['GET',"POST"])
def student_shw(id,title):
    user = User.query.filter_by(id=id).first()
    data = HomeWork.query.filter_by(title=title).first()
    form = SubmitForm()
    homework = Student2Homework.query.filter_by(stu_id=id,title=title).first()

    if form.validate_on_submit():
        data.number += 1
        db.session.add(data)
        #print("ok")
        file = request.files['photo']
        flash("作业提交成功！")
        homework.description = form.description.data
        homework.state = True
        basePath = './static/'+"s/"+str(id)+'/'
        filepath = basePath+file.filename
        homework.file = filepath
        if not os.path.exists(basePath):
            os.makedirs(basePath)
        file.save(filepath)
        db.session.add(homework)
    return render_template('shw.html',form = form,user = user,data=data)


# 实验管理
@app.route('/<int:id>/s/experiment', methods=['POST',"GET"])
def student_page4(id):
    user = User.query.filter_by(id=id).first()
    return render_template('experiment.html',form = 's', act=4,user = user)

# 实训平台
@app.route('/<int:id>/s/train', methods=['POST',"GET"])
def student_page5(id):
    user = User.query.filter_by(id=id).first()
    return render_template('train.html',form = 's', act=5,user = user)



# # 实训平台demo
# @app.route('/p1', methods=['GET'])
# def p1():
#     return render_template('student_main.html', act=1)
# @app.route('/p2', methods=['GET'])
# def p2():
#     return render_template('student_main.html', act=2)
# @app.route('/p3', methods=['GET'])
# def p3():
#     return render_template('student_main.html', act=3)
# @app.route('/p4', methods=['GET'])
# def p4():
#     return render_template('student_main.html', act=4)
# @app.route('/p5', methods=['GET'])
# def p5():
#     return render_template('student_main.html', act=5)





if __name__ == '__main__':
    app.run(debug=True,host='127.0.0.1',port=5000)
