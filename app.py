from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pymysql
import datetime
import jwt

app = Flask(__name__)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'compkey',
    'cursorclass': pymysql.cursors.DictCursor
}

# 创建MySQL连接
connection = pymysql.connect(**db_config)


@app.route('/users/login', methods=['POST'])
def login():
    username = request.args.get('username', None)
    password = request.args.get('password', None)

    try:
        # 创建数据库游标
        with connection.cursor() as cursor:
            # 执行查询
            sql = "SELECT * FROM user WHERE username=%s AND password=%s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()

            if user:
                # 认证成功，返回相应的信息

                secret_key = password

                # 构建 payload
                payload = {
                    'user_name': username,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # 设置过期时间
                }

                # 生成 JWT
                token = jwt.encode(payload, secret_key, algorithm='HS256')

                response_data = {
                    'data': {'token': token},
                    'code': 0,
                    'message': '登录成功'
                }
                return jsonify(response_data)
            else:
                # 认证失败，返回相应的信息
                response_data = {'code': 1, 'message': '登录失败'}
                return jsonify(response_data), 401  # 使用HTTP状态码401表示认证失败
    finally:
        # 关闭数据库连接
        print("success")


@app.route('/users/info', methods=['POST'])
def get_user_info():

    # 连接 MySQL 数据库
    conn = pymysql.connect(
        host='localhost',  # 修改为你的 MySQL 主机名
        user='root',  # 修改为你的 MySQL 用户名
        password='123456',  # 修改为你的 MySQL 密码
        database='compkey'  # 修改为你的数据库名
    )

    # 创建游标对象
    cursor = conn.cursor()

    # 假设已知的 token 值为 'token-admin'
    token = request.args.get('token')
    # 执行查询
    query = "SELECT * FROM user WHERE token = %s"
    cursor.execute(query, (token,))

    # 获取符合条件的用户数据列表
    users = cursor.fetchall()

    # 关闭游标和连接
    cursor.close()
    conn.close()

    if not token:
        return jsonify({"code": 1, "message": "缺少 token 参数"})

    response_data = {
        "data": users,
        "code": 0,
        "message": "获取用户详情成功"
    }

    return jsonify(response_data)


@app.route('/search', methods=['POST'])
def search():
    # 获取POST请求中的search_text参数
    search_text = request.args.get('search_text')

    # 进行一些处理，这里简单地将搜索文本作为竞争性和mid的示例数据
    mid_data = [{"word": search_text, "weight": "0.00023"}]
    competitive_data = [{"word": search_text, "weight": "0.00023"}]

    # 构建返回的JSON数据
    response_data = {
        "data": {
            "mid": mid_data,
            "competitive": competitive_data
        },
        "code": 0,
        "message": "获取竞争性成功"
    }

    # 返回JSON响应
    return jsonify(response_data)


if __name__ == '__main__':
    app.run()
