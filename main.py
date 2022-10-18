#アカウント登録
#ログイン　ログアウト
#セッション管理
#資格情報の登録
#勉強時間の記入
#xampp pass:takumipbl

from flask import Flask, request, redirect, render_template
import MySQLdb
import html
import datetime


def connect():#データベース情報
    con=MySQLdb.connect(
        host="localhost",
        user="root",
        password="takumipbl",
        db="takumi_pbl_database",
        use_unicode=True,
        charset="utf8")
    return con

app=Flask(__name__)#flask

@app.route('/')#初期ページ
def home():
    return render_template("index.html")

@app.route('/nextpage',methods=['get'])#登録ページへの遷移
def go_signup():
    return render_template("signup.html")

@app.route("/signup",methods=['post'])#データベースへのユーザデータ送信
def signup_page():
    id=request.form['id']
    password=request.form['password']
    job=request.form['job']
    license=request.form['license']
    con=connect()
    cur=con.cursor()
    cur.execute("""
                INSERT INTO ユーザテーブル
                (id,job,license,password)
                VALUES(%(id)s,%(job)s,%(license)s,%(password)s)
                """,{"id":id,"job":job,"license":license,"password":password})
    con.commit()
    con.close()
    return render_template('index.html')#多分後で追加

if __name__=='__main__':
    app.debug= True
    app.run(host='localhost')







