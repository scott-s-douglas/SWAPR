from SWAPRsqlite import *

db = SqliteDB("AnonymousCampus.db")
db.cursor.execute("DROP TABLE IF EXISTS assignments")
db.cursor.execute("CREATE TABLE IF NOT EXISTS assignments (row INTEGER PRIMARY KEY NOT NULL, labNumber int, wID text, questionIndex int, URL text)")
db.conn.commit()
db.finalize(3, 3, 3)
db.conn.commit()
