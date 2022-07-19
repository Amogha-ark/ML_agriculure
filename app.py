from flask import Flask, flash, render_template, redirect, url_for, abort, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import sqlite3 
from flask import Flask,render_template,request,redirect,url_for,flash,jsonify,session
from datetime import datetime
from weather import main
import ast
import pickle
import joblib
#####################################################################################
app = Flask(__name__)
# basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
# print(basedir)
# app.config["SQLALCHEMY_DATABASE_URI"] ='sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
d={"rtc":""}
crop_sel = {"Sugarcane": 0,"Rice":0,"Wheat":0,"Onion":0,"Ragi":0,"Jowar":0,"Tomato Maize":0}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

class Farmer(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    rtc = db.Column(db.String(10))
    crop = db.Column(db.String(50))

    def __init__(self,rtc,crop):
        self.rtc=rtc
        self.crop=crop

class Production(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    crops = db.Column(db.String(50))
    value = db.Column(db.Integer)

    def __init__(self,crops,value):
        self.crops = crops
        self.value = value

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('Remember me')

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    
    
########################################################
def update_db(crop,res):
    print(Production.query.all())
    # print(crop)
    ob = Production.query.filter_by(crops=crop).first()
    # print(ob.crops,ob.value)

    if ob:

        ob.value = ob.value + res
        db.session.commit()
    else:
        pre = Production(crop,res)
        db.session.add(pre)
        db.session.commit()


def predict_production(data):
    fi = open("pre_pro.pkl","rb")
    combined = pickle.load(fi)
    fi.close()
    print(data)
    print(combined)
    model = joblib.load("random_forest.joblib")
    x = []
    data[0] = combined.index(data[0].upper())+1
    data[1] = int(data[1])
    data[2] = combined.index(data[2])+1
    data[3] = combined.index(data[3])+1
    data[4] = float(data[4])
    res = model.predict([data])
    print(res)
    return res


def fetch_res():
    get_to = datetime.now().strftime("%Y-%m-%d")
    f = open("data_wth.txt","r")
    data = f.read()
    f.close()
    f = 0
    if len(data)!=0:
    	mydi = ast.literal_eval(data)
    if len(data) == 0 :
        main()
        f=1

    elif not mydi.get(get_to,None):
        main()
        f=1

    else:
        return mydi.get(get_to)

    if f==1:
        f= open('data_wth.txt','r')
        data = f.read()
        mydi=ast.literal_eval(data)
        f.close()
        return mydi.get(get_to)

    return []

@app.route('/previous_crop',methods=['POST','GET'])
def previous_crop():
    if request.method=='POST':
        print(request.form)
        Farmer.query.filter_by(rtc=d['rtc']).delete()
        db.session.commit()

        for cr in request.form:
            print(cr,request.form.get(cr),type(request.form.get(cr)))
            ob = Production.query.filter_by(crops=cr).first()
            print(ob)
            v = float(request.form.get(cr))
            if ob:
                if abs(ob.value-v)>0:
                    ob.value = abs(ob.value - v)
                else:
                    ob.value = v
        db.session.commit()

    ## add this to production db and reduce the production value in the graph
    return redirect(url_for('dashboard'))

@app.route('/predict_data',methods=["POST","GET"])
def predict_data():
    # print(d)
    if request.method == "POST" :
        # print(request.form.get("em1"))
        print(request.form, len(request.form))
        ans = fetch_res()
        print(ans)
        data = []
        data.append(request.form.get("district"))
        data.append(request.form.get("crop_year"))
        data.append(request.form.get("season"))
        data.append(request.form.get("Crop"))
        data.append(request.form.get("area"))
        data = data + ans
        res = predict_production(data)
        print(res)
        res[0] = round(res[0],2)
        dup_check = Farmer.query.filter_by(rtc=d['rtc'],crop=request.form.get("Crop")).first()
        # print(dup_check)
        if len(request.form)>5 and not dup_check:
            #here add to database all the values of the farmer with rtc number and it will redirect to dashboard for graph
            far_data = Farmer(d.get('rtc'),request.form.get("Crop"))
            db.session.add(far_data)
            db.session.commit()
            # res = Farmer.query.all()
            # print(res)

            #Add the predicted value to DB for graph production
            update_db(request.form.get("Crop"),res[0])

            return redirect(url_for('dashboard',msg="Your value added to production"))
        else:
            v=request.form.get("Crop")
            flash(f"You are growing same crop as previous crop !!{v}" , "warning")
        # print(request.form.get("paswd"))
        flash(f"Thanks for submitting !!, your expected production would be {res[0]} tonnes ","success")
        return render_template("predict_data.html",res=res)
    else:
        print("Not enetered",request.method)
        flash("Please fill the feilds","danger")
        return render_template("predict_data.html")

    return render_template("predict_data.html")
    
    
######################################################


@app.route('/')
def index():

    labels = []
    data = []
    ob = Production.query.all()
    if ob:
        for i in ob:
            labels.append(i.crops)
            vv = round((i.value / 10000) * 100,2)
            data.append(vv)
        print(labels, data)
        return render_template("index.html", labels=labels, data=data)
    else:
        # return "No input"
        return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                session['admin'] = True
                return redirect(url_for('dashboard'))

        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    print("---------------------------------------")
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        try:
            new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            flash('Username or Email is already in use.','success')
            print("enetrirjng-----------")
            return redirect(url_for('signup'))
            # return render_template('signup.html', exception=e)
        # #     raise e
        #     abort(500)
            

        return render_template('signup_done.html', new_user=new_user)
        # return '<h1>New user has been created!</h1>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)

@app.route('/dashboard',methods=['GET', 'POST'])
@app.route('/dashboard/<msg>',methods=['GET', 'POST'])
@login_required
def dashboard(msg=None):
    if msg:
        print(msg)
        flash(f"{msg}","warning")
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        if request.form.get('rtc'):
            d["rtc"]=request.form.get('rtc')
            res = Farmer.query.filter_by(rtc=d['rtc']).all()
            if res:
                print(res)
                return render_template('dashboard.html',name=current_user.username,predict=True,res=res)
            else:
                return render_template('dashboard.html', name=current_user.username, predict=True)
        else:
            flash("please enter a valid RTC number ", "danger")
            return render_template('dashboard.html',name=current_user.username,predict=False)
    return render_template('dashboard.html', name=current_user.username,predict=False)

@app.route('/logout')
@login_required
def logout():
    print(session, "---------------------")
    session.pop('admin', None)
    logout_user()


    return redirect(url_for('index'))

@app.route('/graph')
def graph():
    # labels = ['sugarcane','rice','wheat','tomotao']
    # data = [12,10,17,20]
    labels = []
    data=[]
    ob = Production.query.all()
    if ob:
        for i in ob:
            labels.append(i.crops)
            vv = round((i.value / 10000) * 100, 2)
            data.append(vv)
        print(labels,data)
        return render_template("graph.html",labels=labels,data=data)
    else:
        return "No input"

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
