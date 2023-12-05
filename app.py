from flask import Flask, request, jsonify
import pymysql
import datetime
import jwt
from collections import Counter
from pathlib import Path

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
    data=request.get_json()
    username = data.get('username', None)
    password = data.get('password', None)

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
        print("success login:"+str(username))


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

    data =request.get_json()
    # 假设已知的 token 值为 'token-admin'
    token = data.get('token')
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
    data = request.get_json()
    search_text = data.get('search_text')

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
        print("查询" + search_text + "对应的seed_id成功，seed_id为" + str(seed_id))

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
                competitive_data = [{"comp_word": row["comp_word"], "competitiveness": row["competitiveness"]} for row
                                    in results]
                print(competitive_data)

        except Exception as e:
            return jsonify({'error': str(e)})

        finally:
            pass
    else:
        # 查找失败，后端重新计算该词竞争度
        print("查找" + search_text + "对应的seed_id失败, 需要在原始数据集中重新计算")

        midid_list = []  # mid_id列表
        mid_id = 0

        try:
            with connection.cursor() as cursor:
                # 向seed_keys中插入未搜索过的数据
                query = "INSERT INTO seedkeys (seed_word) VALUES (%s)"
                cursor.execute(query, (search_text,))

                # 获取自增的 seed_id
                seed_id = cursor.lastrowid

                # 提交
                connection.commit()
        finally:
            pass
            # print("success")

        # 读取原始文件

        # 获取当前脚本所在的目录
        current_directory = Path(__file__).resolve().parent

        # 构建相对路径
        finaloutput_file_path = current_directory / './data/finaldata.txt'
        cut_finished_file_path = current_directory / './data/cutfinisheddata.txt'

        keyword = search_text

        with open(finaloutput_file_path, 'r', encoding='ANSI', errors='ignore') as input_word, open(
                cut_finished_file_path, 'w',
                encoding='ANSI',
                errors='ignore') as output_word:

            for line in input_word:
                # 检查关键词是否存在于当前行中
                if keyword in line:
                    # 如果包含关键词，将行写入cutfinisheddata.txt
                    output_word.write(line)
        print(f"包含关键词 '{keyword}' 的搜索语句已保存到cutfinisheddata.txt 文件。")

        mid_keyword = current_directory / f"./data/'{keyword}'MidWord.txt"
        # mid_keyword = f"C:\\Users\\28046\\Desktop\\Data\\'{keyword}'MidWord.txt"

        midWordList = []  # 中介关键词列表
        weightList = []  # 权重列表
        a1 = 0  # 所有中介关键词搜索次数

        with open(cut_finished_file_path, 'r', encoding='ANSI', errors='ignore') as input_result, open(
                mid_keyword, 'w',
                encoding='ANSI',
                errors='ignore') as output_result:
            data = input_result.readlines()

            word_counter = Counter()

            for sentence in data:
                if keyword in sentence:
                    words = sentence.split()  # 使用空格分割单词
                    for word in words:
                        if (
                                word != keyword  # 单词不是keyword
                                and keyword not in word  # keyword不作为单词组成部分
                                and len(word) > 1  # 词语长度大于1（同时可以排除特殊符号）
                        ):
                            word_counter[word] += 1

            top_words = word_counter.most_common(6)  # 6为中介关键词词频最高的前6个

            for word, count in top_words:
                a1 += count

            for word, count in top_words:
                weightList.append(count / a1)

                print(f"[中介]{word}: {count}, 权重：", count / a1)

                text = f"[中介]{word}: {count}, 权重：" + str(count / a1) + "\n"

                output_result.write(text)
                midWordList.append(word)

                # 向midkeys插入mid_word和weight
                try:
                    with connection.cursor() as cursor:
                        # 向midkeys中插入数据
                        query2 = "INSERT INTO midkeys (seed_id, mid_word, weight) VALUES (%s,%s,%s)"
                        cursor.execute(query2, (seed_id, word, count / a1,))

                        # 获取自增的 mid_id
                        mid_id = cursor.lastrowid
                        midid_list.append(mid_id)

                        # 提交事务
                        connection.commit()
                finally:
                    pass
                    # print("success")

        competeWordList = []

        with open(finaloutput_file_path, "r", encoding="ANSI") as input_file, \
                open(current_directory / './data/MidWordRelated.txt', "w+", encoding="ANSI") as output_file:
            # 逐行读取
            for line in input_file:
                # 判断当前行是否包含 midWordList 中的任何一个词
                if any(word in line for word in midWordList):
                    # 如果包含至少一个词，将当前行写入 MidWordRalated.txt
                    output_file.write(line)

            print("包含'", keyword, "'的中介关键词的所有搜索语句选择完成, 结果保存在MidWordRelated.txt中")

        with open(current_directory / './data/MidWordRelated.txt', "r", encoding="ANSI") as output_file:
            word_counter = Counter()

            for line in output_file:
                # 分割每一行的文本为单词
                words = line.split()

                # 使用 Counter 统计词频，排除关键词
                for word in words:
                    if (
                            word != keyword  # 单词不是keyword
                            and word not in midWordList
                            and len(word) > 1  # 词语长度大于1（同时可以排除特殊符号）
                    ):
                        word_counter[word] += 1

            # 获取频率最高的6个词
            top_words = word_counter.most_common(6)

            # 打印或保存结果
            for word, count in top_words:
                print("[竞争]", f"{word}: {count}")
                competeWordList.append(word)

        # outComp = []
        comp = 0  # 竞争度
        a = 0  # 中介关键词搜索次数
        ka = 0  # 竞争关键词与中介关键词联合搜索次数
        sa = 0  # 种子关键词与中介关键词联合搜索次数

        with open(current_directory / './data/MidWordRelated.txt', "r", encoding="ANSI") as read_file:
            content = read_file.readlines()
            comp_scores = {}

            # 对每个竞争词单独算一遍竞争度
            for compWord in competeWordList:
                comp = 0
                weightCont = 0  # 权重计数

                #  按midWord权重计算竞争度
                for midWord in midWordList:
                    a = 0
                    sa = 0
                    ka = 0
                    # 遍历每行文本
                    for line in content:
                        if midWord in line:
                            a += 1

                        if compWord in line and midWord in line:
                            ka += 1

                        if keyword in line and midWord in line:
                            sa += 1

                    comp += weightList[weightCont] * (ka / (abs(a - sa) + 1))  # 按权重累加
                comp_scores[compWord] = comp
            # Sort the competition scores in descending order
            sorted_comp_scores = sorted(comp_scores.items(), key=lambda x: x[1], reverse=True)

            # Print the results
            i = 0  # 循环控制，访问midid_list
            for compWord, comp in sorted_comp_scores:
                # 向compkeys中插入数据
                try:
                    with connection.cursor() as cursor:
                        query1 = "INSERT INTO compkeys (mid_id, seed_id, comp_word, competitiveness) VALUES (%s, %s, %s, %s)"
                        cursor.execute(query1, (midid_list[i], seed_id, compWord, comp))

                        # 提交
                        connection.commit()
                finally:
                    pass
                    # print("success")
                # outComp.append((compWord,))
                print(f"{compWord} [竞争度]: {comp}")

                i += 1  # 下一次循环

    # 再次执行数据库查询操作
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
            competitive_data = [{"comp_word": row["comp_word"], "competitiveness": row["competitiveness"]} for
                                row
                                in results]
            print(competitive_data)

    except Exception as e:
        return jsonify({'error': str(e)})

    finally:
        pass

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


# 主函数
if __name__ == '__main__':
    app.run()