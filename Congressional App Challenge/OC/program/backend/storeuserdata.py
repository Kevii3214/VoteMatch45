import sqlite3
#This created userdata.db, is no longer used in actual program
def storedata():
    conn = sqlite3.connect('OC/program/backend/userdata.db')
    c = conn.cursor()
    c.execute("CREATE TABLE userdata (username TEXT,password TEXT);")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    storedata()