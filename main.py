#アカウント登録 できた
#ログイン　ログアウト　できた
#セッション管理　できた
#資格情報の登録　できた  license_idの割り振りが正しくできていない
#勉強時間の記入　できた　変な表示が消えない
#api　検索機能
#xampp pass:takumipbl

import datetime
import html
import secrets
from datetime import timedelta  # セッション管理

import MySQLdb
from flask import Flask, redirect, render_template, request, session, jsonify
from werkzeug.security import check_password_hash as cph  # パスワードの照合
from werkzeug.security import generate_password_hash as gph  # ハッシュ関数の実装

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

@app.after_request#クリックジャッキング対策
def apply_caching(response):
    response.headers["X-Frame-Options"]="SAMEORIGIN"
    return response

app.secret_key=secrets.token_urlsafe(16)#シークレットキーを設定
app.permanent_session_lifetime=timedelta(minutes=60)#セッションの有効期限を設定



@app.route('/')#初期ページ
def home():
    session.clear()
    return render_template("index.html")

@app.route("/mypage")#マイページ 資格の表示　勉強時間の登録表示
def mypage():
    id=session["id"]
    if "id" in session:     
        token=secrets.token_hex()#CSRF対策
        session["mypage"]=token

        con=connect()
        cur=con.cursor()
        cur.execute("""
                    SELECT SUM(work_t) FROM 時間テーブル WHERE id=%(id)s
                    """,{"id":id})
        data=[]
        for row in cur:
            data.append(row)
        if data[0]==0:
            total="未登録"
            return total
        else:
            session["total"]=data[0]
        con.commit()
        con.close()
        return render_template("mypage.html",
                                total=session["total"],
                                id=session["id"],
                                job=html.escape(session["job"]),
                                license=html.escape(session["license"]),
                                user_name=html.escape(session["job"]),token=token
                                )
    else:
        return redirect('login')

@app.route("/time",methods=["GET"])#時間入力ページへ
def time():
    return render_template("time.html",id=session["id"])

@app.route("/to_log", methods=["GET"])
def to_log():
    return render_template("index.html")

@app.route("/to_sch")
def to_sch():
    return render_template("search.html")

@app.route("/to_mp")
def to_mp():
    return render_template("mypage.html")

@app.route("/time_e",methods=['POST'])#勉強時間入力
def time_e():
    if "id" in session:
        if session["mypage"]==request.form["mypage"]:
            id=session["id"]
            work_t=request.form['work_t']
            con=connect()
            cur=con.cursor()
            cur.execute("""
                        INSERT INTO 時間テーブル (id,work_t) VALUEs(%(id)s,%(work_t)s)
                        """,{"id":id,"work_t":work_t})
            con.commit()
            con.close()
            return redirect("mypage")
        else:
            return redirect("mypage")
    else:
        return redirect("login")

@app.route("/signup",methods=['post'])#データベースへのユーザデータ登録 資格テーブルへの資格情報の登録
def signup_page():
    id=request.form['id']
    password=request.form['password']
    job=request.form['job']
    license=request.form['license']
    hashpass=gph(password)
    con=connect()
    cur=con.cursor()
    cur.execute("""
                SELECT * FROM ユーザテーブル WHERE id=%(id)s
                """,{"id":id} )#ID検索
    data=[]
    for row in cur:
            data.append(row)
    if len(data)!=0:
        return render_template("signup.html",msg="既に存在するIDです。")
    con.commit()
    con.close()

    con=connect()#ユーザ登録
    cur=con.cursor()
    cur.execute("""
                INSERT INTO ユーザテーブル
                (id,job,license,password)
                VALUES(%(id)s,%(job)s,%(license)s,%(hashpass)s)
                """,{"id":id,"job":job,"license":license,"hashpass":hashpass})
    con.commit()
    con.close()

    con=connect()#資格登録
    cur=con.cursor()
    cur.execute("""
                INSERT INTO 資格テーブル
                (id,license)
                VALUES(%(id)s,%(license)s)
                """,{"id":id,"license":license})
    con.commit()
    con.close()

    con=connect()
    cur=con.cursor()
    cur.execute("""
                INSERT INTO 時間テーブル
                (id)
                VALUE(%(id)s)
                """,{"id":id})
    con.commit()
    con.close()

    return render_template('index.html',msg="登録完了しました。ログインしてください。")#多分後で追加

@app.route("/login", methods=['get','post'])#ログイン機能
def login():
    if request.method == "GET":
        return render_template('signup.html')

    elif request.method == "POST":
        id=request.form['id']
        session["id"]=id
        password=request.form['password']
        con=connect()
        cur=con.cursor()
        cur.execute("""
                    SELECT password,job,license FROM ユーザテーブル WHERE id=%(id)s
                    """,{"id":id})
        data=[]
        for row in cur:
            data.append([row[0],row[1],row[2]])
        if len(data)==0:
            con.close()
            return render_template("index.html",msg="IDが存在しません")
        if cph(data[0][0],password):
            session["job"]=data[0][1]
            session["license"]=data[0][2]
            con.close()
            return redirect("mypage")
        else:
            con.close()
            return render_template("index.html",msg="パスワードが間違っています")

@app.route("/result",methods=['GET'])
def result():
    name=request.args.get("name")
    form=request.args.get("format")
    con=connect()
    cur=con.cursor()
    cur.execute("""
                SELECT id,job FROM ユーザテーブル WHERE license like %(license)s
                """,{"license":"%"+name+"%"})

    res="<title>検索結果</title>"
    for row in cur:
        res=res+"<table border=\"1\">\n"
        res=res+"\t<tr><td><a href=\"api?id="+html.escape(str(row[0]))+"&"
        res=res+"format="+html.escape(form)+"\">"+html.escape(row[1])+"</a></td></tr>\n"
        #res=res+"\t<tr><td><pre>"+html.escape(row[2])+"</pre></td></tr>"
        res=res+"</table>"
    con.close()
    return res

@app.route("/api")
def api():
    num=request.args.get("id")
    #出来れば追加したい
    form=request.args.get("format")
    con=connect()
    cur=con.cursor()
    cur.execute("""
                SELECT work_t FROM 時間テーブル WHERE id=%(id)s
                """,{"id":num})
    cur2=con.cursor()
    cur2.execute("""
                SELECT id,job FROM ユーザテーブル WHERE id=%(id)s
                """,{"id":num})
    res={}
    for row2 in cur2:
        res['id']=row2[0]
    tmpa=[]
    for row in cur:
        tmpd={}
        tmpd["work_t"]=row[0]
        tmpa.append(tmpd)
    res["study_record"]=tmpa

    return jsonify(res)



if __name__=='__main__':
    app.debug= True
    app.run(host="0.0.0.0")







