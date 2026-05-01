import sqlite3

conn=sqlite3.connect('bank_upi.db')
cursor=conn.cursor()

cursor.execute("""select * from users""")
# cursor.execute("""delete from users where email=?""",("aravind77@gmail.com",))
# cursor.execute("select * from transactions ")
# cursor.execute("drop table transactions")
# cursor.execute("drop table users")

users=cursor.fetchall()
for x in users:
    print(x)

conn.commit()
conn.close()