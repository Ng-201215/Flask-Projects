
import flask
from flask import Flask , render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy

import sqlalchemy
from sqlalchemy import create_engine,text,asc,desc,Table, Column, Integer, String, select
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.sql import exists

from datetime import datetime

import os
os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from io import BytesIO
import base64

Base = declarative_base()

app=Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///tracker.sqlite3"
app.secret_key ='1234'
db=SQLAlchemy(session_options={"autoflush": False})
db.init_app(app)
app.app_context().push()


class Login(db.Model):
    __tablename__ = 'login'
    login_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

class Trackers(db.Model):
    __tablename__ = 'trackers'
    tid = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    ttype = db.Column(db.String, nullable=False)
    userid = db.Column(db.Integer, nullable=False)
    settings=db.Column(db.String)

class Logs(db.Model):
    __tablename__ = 'logs'
    logid = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    time= db.Column(db.String, nullable=False)
    value= db.Column(db.Integer, nullable=False)
    extra=db.Column(db.String)
    trackerid = db.Column(db.Integer, nullable=False)

@app.route("/", methods=['GET','POST'])
def loginpage():
    if (request.method=='GET'):
        return render_template("login.html")

    if (request.method=='POST'):
        name=request.form.get('username')
        pwd=request.form.get('password')
        users=Login.query.filter_by(username=name).first()
        if users:
            if users.password==pwd:
                trackerlist_1=Trackers.query.filter_by(userid=users.login_id).all()
                flash(u'Login Successful !!')
                return render_template("home.html",users=users,tr=trackerlist_1)
            else:
                flash(u'Incorrect password !!')
                return render_template("incorrectpwd.html")
        else:
            new_user=Login(username=name,password=pwd)
            db.session.add(new_user)
            db.session.commit()
            users=Login.query.filter_by(login_id=new_user.login_id).first()
            trackerlist_2=Trackers.query.filter_by(userid=users.login_id).all()
            flash(u'New User detected, Registration Successful !!')
            return render_template("home.html",users=users,tr=trackerlist_2)


@app.route("/addtracker/<int:login_id>", methods=['GET','POST'])
def addtrack(login_id):
    if (request.method=='GET'):
        users=Login.query.filter_by(login_id=login_id).first()
        return render_template("addtrackers.html",users=users)

    elif(request.method=='POST'):
        trname=request.form.get('tname')
        description=request.form.get('desc')
        ttype=request.form.get('tracktype')
        setting=request.form.get('settings')
        users=Login.query.filter_by(login_id=login_id).first()
        if(ttype=='Multiple Choice'):
            mydata=Trackers(name=trname,description=description,ttype=ttype,userid=login_id,settings=setting)
        else:
            mydata=Trackers(name=trname,description=description,ttype=ttype,userid=login_id)
        db.session.add(mydata)
        db.session.commit()

        trackerlist_3=Trackers.query.filter_by(userid=users.login_id).all()
        return render_template("home.html",users=users,tr=trackerlist_3)
    else:
        pass

@app.route("/<int:login_id>/home/update/<name>", methods = ['GET','POST'])
def updatetr(login_id,name):
    users=Login.query.filter_by(login_id=login_id).first()
    trackerdet=Trackers.query.filter_by(userid=login_id,name=name).first()
    if(request.method=='GET'):
        return render_template("update_tracker.html",users=users,tr=trackerdet)
    
    elif(request.method=='POST'):
        trackerdet.name = request.form.get("tname")
        trackerdet.description = request.form.get("desc")
        db.session.commit()
        trackerlist_3=Trackers.query.filter_by(userid=users.login_id).all()
        return render_template("home.html",users=users,tr=trackerlist_3)
    else:
        pass


@app.route("/<int:login_id>/home/delete/<name>",methods=["GET","POST"])
def deletetr(login_id,name):
    users=Login.query.filter_by(login_id=login_id).first()
    trackerdet=Trackers.query.filter_by(userid=login_id,name=name).first()
    tr_logs=Logs.query.filter_by(trackerid=trackerdet.tid).all()
    if (request.method=="GET"):
        db.session.delete(trackerdet)
        for tr in tr_logs:
            db.session.delete(tr)
        db.session.commit()
        trackerlist_3=Trackers.query.filter_by(userid=users.login_id).all()
        return render_template("home.html",users=users,tr=trackerlist_3)


@app.route("/<int:login_id>/home/<name>/addlogs", methods=['GET','POST'])
def Addlogs(login_id,name):
    users=Login.query.filter_by(login_id=login_id).first()
    trackerdet=Trackers.query.filter_by(userid=login_id,name=name).first()
    if(trackerdet.ttype=='Multiple Choice'):
        opt=trackerdet.settings
        my_list = opt.split(",")

    if (request.method=='GET'):    
        if(trackerdet.ttype=='Multiple Choice'):
            return render_template("addlogs.html",users=users,tr=trackerdet,opt=my_list)
        else:
            return render_template("addlogs.html",users=users,tr=trackerdet)

    elif(request.method=='POST'):
        t=datetime.now()
        time=str(t) 
        time_1=request.form.get('times')
        value=request.form.get('valuetracker')
        extra=request.form.get('notes')
        if(len(time_1)==0):
            mydata=Logs(time=time[0:19],value=value,extra=extra,trackerid=trackerdet.tid)
            db.session.add(mydata)
            db.session.commit()
        else:
            mydata=Logs(time=time_1,value=value,extra=extra,trackerid=trackerdet.tid)
            db.session.add(mydata)
            db.session.commit()
        logslist=Logs.query.filter_by(trackerid=trackerdet.tid).all()

        return render_template("logs_homepage.html",users=users,tr=trackerdet,llist=logslist)
    else:
        pass

@app.route("/<int:login_id>/home/<name>", methods=['GET','POST'])
def logs_home(login_id,name):
    users=Login.query.filter_by(login_id=login_id).first()
    trackerdet=Trackers.query.filter_by(userid=login_id,name=name).first()
    logslist=Logs.query.filter_by(trackerid=trackerdet.tid).all()
    return render_template("logs_homepage.html",users=users,tr=trackerdet,llist=logslist)


@app.route("/<int:login_id>/home/<name>/<int:logid>/update", methods = ['GET','POST'])
def updatelog(login_id,name,logid):
    users=Login.query.filter_by(login_id=login_id).first()
    trackerdet=Trackers.query.filter_by(userid=login_id,name=name).first()
    logval=Logs.query.filter_by(trackerid=trackerdet.tid,logid=logid).first()
    if(trackerdet.ttype=='Multiple Choice'):
        opt=trackerdet.settings
        my_list = opt.split(",")
        
    if(request.method=='GET'):
        if(trackerdet.ttype=='Multiple Choice'):
            return render_template("update_log.html",users=users,tr=trackerdet,lv=logval,opt=my_list)
        else:
            return render_template("update_log.html",users=users,tr=trackerdet,lv=logval)
            
    elif(request.method=='POST'):
        t=request.form.get("time")
        if(len(t)!=0):
            logval.time = request.form.get("time")

        logval.value = request.form.get("valuetracker")
        logval.extra= request.form.get('note')
        db.session.commit()
        logslist=Logs.query.filter_by(trackerid=trackerdet.tid).all()
        return render_template("logs_homepage.html",users=users,tr=trackerdet,llist=logslist)
    else:
        pass


@app.route("/<int:login_id>/home/<name>/<int:logid>/delete",methods=["GET","POST"])
def deletelog(login_id,name,logid):
    users=Login.query.filter_by(login_id=login_id).first()
    trackerdet=Trackers.query.filter_by(userid=login_id,name=name).first()
    logval=Logs.query.filter_by(trackerid=trackerdet.tid,logid=logid).first()
    if (request.method=="GET"):
        db.session.delete(logval)
        db.session.commit()
        logslist=Logs.query.filter_by(trackerid=trackerdet.tid).all()
        return render_template("logs_homepage.html",users=users,tr=trackerdet,llist=logslist)


@app.route("/<int:login_id>/home/<name>/trendline",methods=["GET","POST"])
def trendline(login_id,name):
    users=Login.query.filter_by(login_id=login_id).first()
    trackerdet=Trackers.query.filter_by(userid=login_id,name=name).first()
    t=Logs.query.filter_by(trackerid=trackerdet.tid).all()

    a,b=[],[]
    for r in t:
        a.append(r.time)
        b.append(r.value)  
    
    if(trackerdet.ttype=="Numerical"):
        res = {}
        for key in a:
            for value in b:
                res[key] = int(value)
                b.remove(value)
                break
        c,d,e=[],[],[]
        c=dict(sorted(res.items()))
        d=list(c.keys())
        e=list(c.values())
        plt.plot(d,e)
        plt.xlabel("Time")

    if(trackerdet.ttype=="Character- Yes or No"):
        yv,nv=0,0
        for i in b:
            if(i=="Yes"):
                yv+=1
            else:
                nv+=1
        opt=['Yes','No']
        ynvalues=[yv,nv]
        plt.bar(opt,ynvalues,color='pink',width=0.9) 

        mini = 0
        maxi = max(ynvalues)+1
        yint=range(mini,maxi)
        plt.yticks(yint)
        plt.xlabel('Options')

    if(trackerdet.ttype=="Multiple Choice"):
        opt=trackerdet.settings
        my_list = opt.split(",")
        mcq={}
        types,tvalues=[],[]
        for i in my_list:
            mcq.update({i:0})
        for j in b:
                mcq[j]+=1
        types=list(mcq.keys())
        tvalues=list(mcq.values())
        plt.bar(types,tvalues,color='pink',width=0.9)
 
        mini = 0
        maxi = max(tvalues) + 1
        yint=range(mini,maxi)
        plt.yticks(yint)
        plt.xlabel('Options')

    plt.title(str(name)+" tracker graph")
    plt.ylabel('value')
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('trendline.html',plot_url=plot_url,users=users,tr=trackerdet)

@app.route("/<username>/home", methods=['GET','POST'])
def home(username):
    users=Login.query.filter_by(username=username).first()
    trackerdet=Trackers.query.filter_by(userid=users.login_id).all()
    return render_template("home.html",users=users,tr=trackerdet)

if __name__ == '__main__':
    app.run(debug=True)

