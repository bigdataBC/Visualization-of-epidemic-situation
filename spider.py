from selenium.webdriver import Chrome, ChromeOptions
import requests
import pymysql
import time
import json
import traceback
import sys

def get_conn():
    """
    :return: 连接，游标
    """
    # 创建连接
    conn = pymysql.connect(host="127.0.0.1",
                           user="root",
                           password="123456",
                           db="cov",
                           charset="utf8")
    # 创建游标
    cursor = conn.cursor()  # 执行完毕返回的结果集默认以元组显示
    return conn, cursor


def close_conn(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()


def get_tencent_data():
    """
    :return: 返回历史数据和当日详细数据
    """
    url = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5'
    url_his = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_other'  # 加上这个history大兄弟++++++++

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    }
    r = requests.get(url, headers)
    res = json.loads(r.text)  # json字符串转字典
    data_all = json.loads(res['data'])

    # 再加上history的配套东东++++++++
    r_his = requests.get(url_his, headers)
    res_his = json.loads(r_his.text)
    data_his = json.loads(res_his['data'])

    history = {}  # 历史数据
    #     for i in data_all["chinaDayList"]:
    #         ds = "2020." + i["date"]
    #         tup = time.strptime(ds, "%Y.%m.%d")
    #         ds = time.strftime("%Y-%m-%d", tup)  # 改变时间格式,不然插入数据库会报错，数据库是datetime类型
    #         confirm = i["confirm"]
    #         suspect = i["suspect"]
    #         heal = i["heal"]
    #         dead = i["dead"]
    #         history[ds] = {"confirm": confirm, "suspect": suspect, "heal": heal, "dead": dead}
    #     for i in data_all["chinaDayAddList"]:
    #         ds = "2020." + i["date"]
    #         tup = time.strptime(ds, "%Y.%m.%d")
    #         ds = time.strftime("%Y-%m-%d", tup)
    #         confirm = i["confirm"]
    #         suspect = i["suspect"]
    #         heal = i["heal"]
    #         dead = i["dead"]
    #         history[ds].update({"confirm_add": confirm, "suspect_add": suspect, "heal_add": heal, "dead_add": dead})

    # 通过上面的代码肯定不行了，里面只有当日详细数据，修改也很简单，改一下循环遍历的数据源即可：++++
    for i in data_his["chinaDayList"]:
        ds = "2020." + i["date"]
        tup = time.strptime(ds, "%Y.%m.%d")
        ds = time.strftime("%Y-%m-%d", tup)  # 改变时间格式,不然插入数据库会报错，数据库是datetime类型
        confirm = i["confirm"]
        suspect = i["suspect"]
        heal = i["heal"]
        dead = i["dead"]
        history[ds] = {"confirm": confirm, "suspect": suspect, "heal": heal, "dead": dead}
    for i in data_his["chinaDayAddList"]:
        ds = "2020." + i["date"]
        tup = time.strptime(ds, "%Y.%m.%d")
        ds = time.strftime("%Y-%m-%d", tup)
        confirm = i["confirm"]
        suspect = i["suspect"]
        heal = i["heal"]
        dead = i["dead"]
        history[ds].update({"confirm_add": confirm, "suspect_add": suspect, "heal_add": heal, "dead_add": dead})

    # 下面就不用动了
    details = []  # 当日详细数据
    update_time = data_all["lastUpdateTime"]
    data_country = data_all["areaTree"]  # list 25个国家
    data_province = data_country[0]["children"]  # 中国各省
    for pro_infos in data_province:
        province = pro_infos["name"]  # 省名
        for city_infos in pro_infos["children"]:
            city = city_infos["name"]
            confirm = city_infos["total"]["confirm"]
            confirm_add = city_infos["today"]["confirm"]
            heal = city_infos["total"]["heal"]
            dead = city_infos["total"]["dead"]
            details.append([update_time, province, city, confirm, confirm_add, heal, dead])
    return history, details


def get_baidu_hot():
    """
    :return: 返回百度疫情热搜
    """
    option = ChromeOptions()  # 创建谷歌浏览器实例
    option.add_argument("--headless")  # 隐藏浏览器
    option.add_argument('--no-sandbox')

    url = "https://voice.baidu.com/act/virussearch/virussearch?from=osari_map&tab=0&infomore=1"
    browser = Chrome(options=option,executable_path="./chromedriver.exe")
    browser.get(url)
    # 找到展开按钮
    # dl = browser.find_element_by_xpath('//*[@id="ptab-0"]/div/div[2]/section/div')
    dl = browser.find_element_by_xpath('//*[@id="ptab-0"]/div/div[1]/section/div')
    dl.click()
    time.sleep(1)
    # 找到热搜标签
    # c = browser.find_elements_by_xpath('//*[@id="ptab-0"]/div/div[2]/section/a/div/span[2]')
    c = browser.find_elements_by_xpath('//*[@id="ptab-0"]/div/div[1]/section/a/div/span[2]')
    context = [i.text for i in c]  # 获取标签内容
    print(context)
    return context


def update_hotsearch():
    """
    将疫情热搜插入数据库
    :return:
    """
    cursor = None
    conn = None
    try:
        context = get_baidu_hot()
        print(f"{time.asctime()}开始更新热搜数据")
        conn, cursor = get_conn()
        sql = "insert into hotsearch(dt,content) values(%s,%s)"
        ts = time.strftime("%Y-%m-%d %X")
        for i in context:
            cursor.execute(sql, (ts, i))  # 插入数据
        conn.commit()  # 提交事务保存数据
        print(f"{time.asctime()}数据更新完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


def update_hotsearch():
    """
    将疫情热搜插入数据库
    :return:
    """
    cursor = None
    conn = None
    try:
        context = get_baidu_hot()
        print(f"{time.asctime()}开始更新热搜数据")
        conn, cursor = get_conn()
        sql = "insert into hotsearch(dt,content) values(%s,%s)"
        ts = time.strftime("%Y-%m-%d %X")
        for i in context:
            cursor.execute(sql, (ts, i))  # 插入数据
        conn.commit()  # 提交事务保存数据
        print(f"{time.asctime()}数据更新完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


def update_details():
    """
    更新 details 表
    :return:
    """
    cursor = None
    conn = None
    try:
        li = get_tencent_data()[1]  #  0 是历史数据字典,1 最新详细数据列表
        conn, cursor = get_conn()
        sql = "insert into details(update_time,province,city,confirm,confirm_add,heal,dead) values(%s,%s,%s,%s,%s,%s,%s)"
        sql_query = 'select %s=(select update_time from details order by id desc limit 1)' #对比当前最大时间戳
        cursor.execute(sql_query,li[0][0])
        if not cursor.fetchone()[0]:
            print(f"{time.asctime()}开始更新最新数据")
            for item in li:
                cursor.execute(sql, item)
            conn.commit()  # 提交事务 update delete insert操作
            print(f"{time.asctime()}更新最新数据完毕")
        else:
            print(f"{time.asctime()}已是最新数据！")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


def insert_history():
    """
        插入历史数据
    :return:
    """
    cursor = None
    conn = None
    try:
        dic = get_tencent_data()[0]  # 0 是历史数据字典,1 最新详细数据列表
        print(f"{time.asctime()}开始插入历史数据")
        conn, cursor = get_conn()
        sql = "insert into history values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for k, v in dic.items():
            # item 格式 {'2020-01-13': {'confirm': 41, 'suspect': 0, 'heal': 0, 'dead': 1}
            cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
                                 v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
                                 v.get("dead"), v.get("dead_add")])

        conn.commit()  # 提交事务 update delete insert操作
        print(f"{time.asctime()}插入历史数据完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


def update_history():
    """
    更新历史数据
    :return:
    """
    cursor = None
    conn = None
    try:
        dic = get_tencent_data()[0]  #  0 是历史数据字典,1 最新详细数据列表
        print(f"{time.asctime()}开始更新历史数据")
        conn, cursor = get_conn()
        sql = "insert into history values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        sql_query = "select confirm from history where ds=%s"
        for k, v in dic.items():
            # item 格式 {'2020-01-13': {'confirm': 41, 'suspect': 0, 'heal': 0, 'dead': 1}
            if not cursor.execute(sql_query, k):
                cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
                                     v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
                                     v.get("dead"), v.get("dead_add")])
        conn.commit()  # 提交事务 update delete insert操作
        print(f"{time.asctime()}历史数据更新完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


if __name__ == "__main__":
    # l = len(sys.argv)
    # if l == 1:
    #     s = """
    #     请输入参数
    #     参数说明：
    #     up_his  更新历史记录表
    #     up_hot  更新实时热搜
    #     up_det  更新详细表
    #     """
    #     print(s)
    # else:
    #     order = sys.argv[1]
    #     if order == "up_his":
    #         update_history()
    #     elif order == "up_det":
    #         update_details()
    #     elif order == "up_hot":
    #         update_hotsearch()

    update_history()
    update_details()
    update_hotsearch()


