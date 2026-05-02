from flask import Flask, render_template, redirect,request,session,make_response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app=Flask(__name__)
app.secret_key = 'aravind_bank_upi_secret_key'

def create_table_users():
    conn=sqlite3.connect("bank_upi.db")
    cursor=conn.cursor()

    cursor.execute("""
                    create table if not exists users(
                        user_name text not null,
                        email text primary key,
                        password text not null,
                        user_id varchar(20),
                        balance real not null
                    )
                   """)

    conn.commit()
    conn.close()

create_table_users()

def create_table_transactions():
    conn=sqlite3.connect("bank_upi.db")
    cursor=conn.cursor()

    cursor.execute("""
                    create table if not exists transactions(
                        transaction_id integer primary key autoincrement,
                        receiver_name text not null,
                        receiver_id varchar(20) not null,
                        sender_name text not null,
                        sender_id varchar(20) not null,
                        previous_balance_receiver real not null,
                        previous_balance_sender real not null,
                        send_money real not null,
                        receiver_balance real not null,
                        sender_balance real not null
                   )
                   """)
    
    conn.commit()
    conn.close()

create_table_transactions()

@app.route('/',methods=["GET","POST"])
def createbankaccount():
    if request.method=="GET":
        return render_template("create_bank_account.html")
    elif request.method=="POST":

        name = request.form['user_name']
        email = request.form['email']
        password = request.form['password']
        hash_password=generate_password_hash(password)

        conn=sqlite3.connect('bank_upi.db')
        cursor=conn.cursor()

        cursor.execute('insert into users(user_name,email,password,balance) values(?,?,?,?)',(name,email,hash_password,0))

        user_id1=cursor.lastrowid
        user_id="AGBANK"+str(user_id1).zfill(3)

        cursor.execute("update users set user_id=? where email=?",(user_id,email))

        cursor.execute("""select password,balance, user_name, user_id from users where email=?""",(email,))
        user_details = cursor.fetchone()
        if user_details:
            session['user_details']={
                'user_name': user_details[2],
                'email': email,
                'user_id': user_details[3],
                'balance': user_details[1]
            }


        conn.commit()
        conn.close()

        return redirect("/main_screen")
    return render_template("create_bank_account.html")

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=='GET':
        session.clear()
        return render_template('login_page.html')
    elif request.method=="POST":

        email=request.form['email']
        password=request.form['password']

        conn=sqlite3.connect('bank_upi.db')
        cursor=conn.cursor()

        cursor.execute("""select password,balance, user_name, user_id from users where email=?""",(email,))
        hash_password=cursor.fetchone()
        if hash_password:
            session['user_details']={
                'user_name': hash_password[2],
                'email': email,
                'user_id': hash_password[3],
                'balance': hash_password[1]
            }

        conn.commit()
        conn.close()

        if hash_password and check_password_hash(hash_password[0],password):
            return redirect('/main_screen')
        else:
            return redirect('/login')

@app.route('/main_screen',methods=["GET","POST"])
def mainscreen():
    return render_template("main_screen.html")

@app.route('/home_page')
def home_page():
    user_details = session.get('user_details')
    if not user_details:
        return make_response("""
                <script>
                    window.top.location.href = '/login';
                </script>
            """)
    
    return render_template("home_page.html", user_name=session['user_details'].get('user_name'), user_id=session['user_details'].get('user_id'), balance=session['user_details'].get('balance'))

@app.route('/transfer_page',methods=["GET","POST"])
def transfer_page():
    if request.method=="GET":
        return render_template("transfer_page.html",message=False)
    if request.method=="POST":
        email = request.form["email"]
        password=request.form["password"]
        amount=float(request.form["amount"])

        email_receiver_by_sender=request.form["email_receiver_by_sender"]

        conn=sqlite3.connect('bank_upi.db')
        cursor=conn.cursor()

        cursor.execute("""select user_name,email,password,user_id,balance from users where email=?""",(email,))
        output=cursor.fetchone()

        username=output[0]
        email=output[1]
        originalpassword=output[2]
        userid=output[3]
        current_balance=output[4]

        cursor.execute("""select user_name,email,password,user_id,balance from users where email=?""",(email_receiver_by_sender,))
        receiver_output=cursor.fetchone()

        username_receiver=receiver_output[0]
        email_receiver=receiver_output[1]
        # originalpassword_receiver=receiver_output[2]
        userid_receiver=receiver_output[3]
        current_balance_receiver=receiver_output[4]

        if output and check_password_hash(originalpassword,password):
            if email != email_receiver_by_sender:
                if session['user_details']['email']==email:
                    if amount<=current_balance:
                        final_amount = current_balance - amount
                        final_amount_by_receiver = current_balance_receiver + amount
                        cursor.execute("""update users set balance = ? where email=?""",(final_amount,email))

                        cursor.execute("""insert into transactions(receiver_name,receiver_id,sender_name,sender_id,previous_balance_receiver,previous_balance_sender,send_money,receiver_balance,sender_balance) values(?,?,?,?,?,?,?,?,?)""",(username_receiver,userid_receiver,username,userid,current_balance_receiver,current_balance,amount,final_amount_by_receiver,final_amount)) 

                        cursor.execute("""update users set balance = ? where email=?""",(final_amount_by_receiver,email_receiver_by_sender))

                        session['user_details']['balance'] = final_amount
                        session.modified = True
                    
                    else:
                        return render_template("transfer_page.html",message=False,show_error=True,error="Insufficient balance")
                else:
                    return render_template("transfer_page.html",message=False,show_error=True,error="This is not your account, Please login with your account to transfer money")
            else:
                    return render_template("transfer_page.html",message=False,show_error=True,error="This is transaction can only be done from your account which is currently logged in to other account , Please go to deposite page")
        else:
            return render_template("transfer_page.html",message=False,show_error=True,error="Invalid email or password")

        conn.commit()
        conn.close()

        return render_template("transfer_page.html",message=True,show_error=False,username=username,email=email,user_id=userid,money_transferred=amount,current_money_sender=final_amount,username_receiver=username_receiver,email_receiver=email_receiver,user_id_receiver=userid_receiver,current_money_receiver=final_amount_by_receiver)

@app.route('/deposit',methods=["GET","POST"])
def deposit():
    if request.method=="GET":
        return render_template("deposit_page.html",message=False,show_error=False)
    if request.method=="POST":
        email = request.form["email"]
        password=request.form["password"]
        amount=float(request.form["amount"])

        conn=sqlite3.connect('bank_upi.db')
        cursor=conn.cursor()

        cursor.execute("""select user_name,email,password,user_id,balance from users where email=?""",(email,))
        output=cursor.fetchone()

        username=output[0]
        email=output[1]
        originalpassword=output[2]
        userid=output[3]
        current_balance=output[4]

        if output and check_password_hash(originalpassword,password):
            if session['user_details']['email']==email:
                final_amount = current_balance + amount
            
                cursor.execute("""update users set balance = ? where email=?""",(final_amount,email))

                cursor.execute("""insert into transactions(receiver_name,receiver_id,sender_name,sender_id,previous_balance_receiver,previous_balance_sender,send_money,receiver_balance,sender_balance) values(?,?,?,?,?,?,?,?,?)""",(username,userid,username,userid,current_balance,current_balance,amount,final_amount,final_amount))

                session['user_details']['balance'] = final_amount
                session.modified = True

            else:
                return render_template("deposit_page.html",message=False,show_error=True,error="This is not your account, Please login with your account to deposite money , If you want to deposite money to other account please go to transfer page")
        else:
            return render_template("deposit_page.html",message=False,show_error=True,error="Invalid email or password")

        conn.commit()
        conn.close()

        return render_template(
            "deposit_page.html",
            message=True,
            username=username,
            email=email,
            user_id=userid
        )
    
@app.route('/check_transactions')
def check_transaction():

    # conn=sqlite3.connect('bank_upi.db')
    # cursor=conn.cursor()

    # cursor.execute("""select * from transactions where sender_id=? or receiver_id=? order by transaction_id desc""",(session['user_details'].get('user_id'),session['user_details'].get('user_id')))
    # transactions=cursor.fetchall()
    # print(transactions)

    # conn.commit()
    # conn.close()

    # return render_template("check_transactions.html", transactions=transactions)
    return render_template("check_transactions.html")
    # return redirect('/all_transactions')

@app.route('/all_transactions')
def all_transactions():

    conn=sqlite3.connect('bank_upi.db')
    cursor=conn.cursor()

    cursor.execute("""select transaction_id,
                        receiver_name,
                        receiver_id,
                        sender_name,
                        sender_id,
                        previous_balance_receiver,
                        previous_balance_sender,
                        send_money,
                        receiver_balance,
                        sender_balance from transactions where sender_id=? or receiver_id=? order by transaction_id desc""",(session['user_details'].get('user_id'),session['user_details'].get('user_id')))
    transactions=cursor.fetchall()

    conn.commit()
    conn.close()

    return render_template("all_transactions.html", transactions=transactions,sender_user_id=session['user_details'].get('user_id') )

@app.route('/sent_transactions')
def sent_transactions():

    conn=sqlite3.connect('bank_upi.db')
    cursor=conn.cursor()

    cursor.execute("""select * from transactions where sender_id=? and receiver_id<>? order by transaction_id desc""",(session['user_details'].get('user_id'), session['user_details'].get('user_id')))
    transactions=cursor.fetchall()

    conn.commit()
    conn.close()

    return render_template("sent_transactions.html", transactions=transactions, sender_user_id=session['user_details'].get('user_id') )

@app.route('/received_transactions')
def received_transactions():

    conn=sqlite3.connect('bank_upi.db')
    cursor=conn.cursor()

    cursor.execute("""select * from transactions where receiver_id=? order by transaction_id desc""",(session['user_details'].get('user_id'),))
    transactions=cursor.fetchall()

    conn.commit()
    conn.close()

    return render_template("received_transactions.html", transactions=transactions, receiver_user_id=session['user_details'].get('user_id'))

@app.route('/check_balance')
def check_balance():
    return render_template("check_balance.html",balance=session['user_details'].get('balance'))


if __name__=="__main__":
    # app.run(host='0.0.0.0',port=int(os.environ.get("PORT",5000)))
    app.run(debug=True)