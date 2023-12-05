from flask import Flask, request, jsonify
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

    # 记录搜索请求
    try:
        # 创建游标对象
        with connection.cursor() as cursor:
            # 执行插入语句
            user_id = 1
            query = f"INSERT INTO search_records (user_id, search_text) VALUES ({user_id},'{search_text}')"
            cursor.execute(query)

            # 提交事务
            connection.commit()
    except pymysql.Error as e:
        # 捕获 pymysql.Error 异常
        print(f"Error: {e}")
        connection.rollback()  # 发生异常时回滚事务
    except Exception as e:
        # 捕获其他异常
        print(f"Unexpected error: {e}")
        connection.rollback()  # 发生异常时回滚事务
    finally:
        pass

    seed_id = 0

    # 种子关键词是否已经过查找,默认没有
    if_seed_id_found = False

    # 查找关键词的seed_id
    try:
        with connection.cursor() as cursor:
            # 执行查询，选择seed_id列
            sql = "SELECT seed_id FROM seedkeys WHERE seed_word = %s"
            cursor.execute(sql, (search_text,))
            result = cursor.fetchone()

            if result:
                seed_id = result['seed_id']
                if_seed_id_found = True
            else:
                # print("查找失败")
                pass
    finally:
        # print("success")
        pass

    mid_data = ''
    competitive_data = ''
    # 若查找到对应的seed_id，则执行进一步查询,提取数据库已有信息
    if if_seed_id_found:
        print("查询"+search_text+"对应的seed_id成功，seed_id为"+str(seed_id))

        # 查询中介关键词
        try:
            with connection.cursor() as cursor:
                # 执行查询，选择mid_word和weight列
                sql = "SELECT mid_word, weight FROM midkeys WHERE seed_id = %s"
                cursor.execute(sql, (seed_id,))
                results = cursor.fetchall()

                # 查询结果转换
                mid_data = [{"word": row["mid_word"], "weight": row["weight"]} for row in results]
                print(mid_data)
        finally:
            pass
            # print("success")

        # 查询竞争关键词
        try:
            with connection.cursor() as cursor:
                # 执行查询语句
                sql1 = "SELECT comp_word, competitiveness FROM compkeys WHERE seed_id = %s"
                cursor.execute(sql1, args=seed_id)

                # 获取查询结果
                results = cursor.fetchall()

                # 查询结果转换
                competitive_data = [{"comp_word": row["comp_word"], "competitiveness": row["competitiveness"]} for row in results]
                print(competitive_data)

        except Exception as e:
            return jsonify({'error': str(e)})

        finally:
            pass
    else:
        # 查找失败，建立新映射
        print("查找"+search_text+"对应的seed_id失败, 需要在原始数据集中重新筛选")


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
