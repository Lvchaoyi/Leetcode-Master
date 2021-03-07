import json
import os
import sys
import time
import pandas as pd
from pathlib import Path
import requests


class LCHelper(object):
    """
    包含lc的相关功能
    """

    @staticmethod
    def login(email, password):
        """
        lc登录，返回登录会话
        :param email:
        :param password:
        :return: session
        """
        session = requests.Session()  # 建立会话
        session.encoding = "utf-8"

        login_data = {
            'login': email,
            'password': password
        }
        # 浏览器标识
        user_agent = r"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)"
        # 登陆网址
        sign_in_url = 'https://leetcode-cn.com/accounts/login/'
        # lc网址
        lc_url = 'https://leetcode-cn.com/'
        headers = {'User-Agent': user_agent, 'Connection': 'keep-alive',
                   'Referer': sign_in_url, "origin": lc_url}

        # 发送登录请求
        session.post(sign_in_url, headers=headers, data=login_data,
                     timeout=10, allow_redirects=False)
        session_str = "LEETCODE_SESSION"
        is_login = session.cookies.get(session_str) is not None
        if is_login:
            print("Login successfully!")
            return session
        else:
            print("Login failed!")

    @staticmethod
    def get_submissions(session, num: int) -> dict:
        """
        获取LC提交记录
        :param session:
        :param num:
        :return:
        """
        submissions_dic = {}
        n = num // 20 if not num % 20 else num // 20 + 1
        last_key = ""
        for _ in range(n):
            # LC每次默认获取lastKey后的20条记录
            url = f"https://leetcode-cn.com/api/submissions/?lastkey={last_key}"
            res = session.get(url)
            res_json = json.loads(res.content.decode('utf-8'))
            submissions = res_json["submissions_dump"]
            has_next = res_json["has_next"]
            last_key = res_json["last_key"] if has_next else ""
            for submission in submissions:
                print(submission)
                title_cn = submission["title"]
                # 只保留最新的一份ac
                if title_cn in submissions_dic:
                    continue
                # 除去非ac的部分提交
                if submission["status_display"] == "Accepted":
                    submissions_dic[title_cn] = submission
                else:
                    continue
            if not has_next:
                break
            time.sleep(1)  # 必须加延时，不然会报错“没有权限”
        # print(submissions_dic)
        return submissions_dic


if __name__ == '__main__':
    session = LCHelper().login("18607113727", "sb1995~")
    print(LCHelper.get_submissions(session, 10))
