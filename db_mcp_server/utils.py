import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "../../Ecommerce.db")

"""
    LLM 生成SQL字符串
    utils.query(sql) 拿着这个字符串去数据库跑
    返回结果
"""
def query(sql):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [desc[0] for desc in cursor.description]
    res = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return res


if __name__ == "__main__":
    sql = "SELECT * FROM Product LIMIT 5;"
    res = query(sql)
    for row in res:
        print(row)
