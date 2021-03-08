import json
import os
import sys
import time
import pandas as pd
from pathlib import Path
import requests

# TODO 2.获取题目标签

class LCHelper(object):
    '''
    包含lc的相关功能
    '''

    @staticmethod
    def login(email, password):
        '''
        lc登录，返回登录会话
        :param email:
        :param password:
        :return: session
        '''
        session = requests.Session()  # 建立会话
        session.encoding = 'utf-8'

        login_data = {
            'login': email,
            'password': password
        }
        # 浏览器标识
        user_agent = r'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
        # 登陆网址
        sign_in_url = 'https://leetcode-cn.com/accounts/login/'
        # lc网址
        lc_url = 'https://leetcode-cn.com/'
        headers = {'User-Agent': user_agent, 'Connection': 'keep-alive',
                   'Referer': sign_in_url, 'origin': lc_url}

        # 发送登录请求
        session.post(sign_in_url, headers=headers, data=login_data,
                     timeout=10, allow_redirects=False)
        session_str = 'LEETCODE_SESSION'
        is_login = session.cookies.get(session_str) is not None
        if is_login:
            print('Login successfully!')
            return session
        else:
            print('Login failed!')

    def get_submissions(self, session, num: int) -> dict:
        '''
        获取LC提交记录
        :param session:
        :param num:
        :return:
        '''
        all_submissions = []
        n = num // 20 if not num % 20 else num // 20 + 1
        last_key = ''
        for _ in range(n):
            # LC每次默认获取lastKey后的20条记录
            url = f'https://leetcode-cn.com/api/submissions/?lastkey={last_key}'
            res = session.get(url)
            res_json = json.loads(res.content.decode('utf-8'))
            submissions = res_json['submissions_dump']
            has_next = res_json['has_next']
            last_key = res_json['last_key'] if has_next else ''
            all_submissions.extend(submissions)
            # for submission in submissions:
            #     print(submission)
            #     title_cn = submission['title']
            #     # 只保留最新的一份ac
            #     if title_cn in submissions_dic:
            #         continue
            #     # 除去非ac的部分提交
            #     if submission['status_display'] == 'Accepted':
            #         submissions_dic[title_cn] = submission
            #     else:
            #         continue
            # if not has_next:
            #     break
            time.sleep(1)  # 必须加延时，不然会报错“没有权限”
        return all_submissions

    def get_accepted_problems(self, session):
        user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36' \
                     r' (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
        url = 'https://leetcode-cn.com/graphql'
        params = {'operationName': 'userProfileQuestions',
                  'variables': {'status':'ACCEPTED','skip':0,'first':1000,'sortField':'LAST_SUBMITTED_AT','sortOrder':'DESCENDING','difficulty':[]},
                  'query': "query userProfileQuestions($status: StatusFilterEnum!, $skip: Int!, $first: Int!, $sortField: SortFieldEnum!, $sortOrder: SortingOrderEnum!, $keyword: String, $difficulty: [DifficultyEnum!]) {\n  userProfileQuestions(status: $status, skip: $skip, first: $first, sortField: $sortField, sortOrder: $sortOrder, keyword: $keyword, difficulty: $difficulty) {\n    totalNum\n    questions {\n      translatedTitle\n      frontendId\n      titleSlug\n      title\n      difficulty\n      lastSubmittedAt\n      numSubmitted\n      lastSubmissionSrc {\n        sourceType\n        ... on SubmissionSrcLeetbookNode {\n          slug\n          title\n          pageId\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
                  }

        json_data = json.dumps(params).encode('utf8')

        headers = {
            'User-Agent': user_agent,
            'Connection':'keep-alive',
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode-cn.com/progress/'
        }
        resp = session.post(url, data=json_data, headers=headers, timeout=10)
        content = resp.json()
        # 题目详细信息
        questions = content['data']['userProfileQuestions']['questions']
        print(questions)
        return questions

    @staticmethod
    def get_problem_id_slug_map():
        session = requests.Session()
        user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36' \
                     r' (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
        url = 'https://leetcode-cn.com/api/problems/all/'
        headers = {'User-Agent': user_agent, 'Connection': 'keep-alive'}
        resp = session.get(url, headers=headers, timeout=10)
        question_list = json.loads(resp.content.decode('utf-8'))
        for question in question_list['stat_status_pairs']:
            print(question)
            # 题目编号
            question_id = question['stat']['question_id']
            # 题目名称
            question_slug = question['stat']['question__title_slug']
            # 题目状态
            question_status = question['status']
            # 题目难度级别，1 为简单，2 为中等，3 为困难
            level = question['difficulty']['level']
            # 是否为付费题目
            if question['paid_only']:
                continue
        return {str(_['stat']['question_id']): _['stat']['question__title_slug'] for _ in question_list['stat_status_pairs']}

    @staticmethod
    def get_problem_by_slug(slug):
        session = requests.Session()
        user_agent = r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36' \
                     r' (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
        url = 'https://leetcode-cn.com/graphql'
        params = {'operationName': 'getQuestionDetail',
                  'variables': {'titleSlug': slug},
                  'query': '''query getQuestionDetail($titleSlug: String!) {
                question(titleSlug: $titleSlug) {
                    questionId
                    questionFrontendId
                    questionTitle
                    questionTitleSlug
                    content
                    difficulty
                    stats
                    similarQuestions
                    categoryTitle
                    topicTags {
                            name
                            slug
                    }
                }
            }'''
                  }

        json_data = json.dumps(params).encode('utf8')

        headers = {
            'User-Agent': user_agent,
            'Connection':'keep-alive',
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode-cn.com/problems/'
        }
        resp = session.post(url, data=json_data, headers=headers, timeout=10)
        content = resp.json()
        # 题目详细信息
        if 'data' not in content:
            print(content)
            return None
        question = content['data']['question']
        return question


if __name__ == '__main__':
    lc_helper = LCHelper()
    # lc_helper.get_problem_by_slug('simplify-path')

    session = lc_helper.login('18607113727', 'sb1995~')
    id_slug_map = lc_helper.get_problem_id_slug_map()
    accepted_problems = lc_helper.get_accepted_problems(session)
    accepted_problem_slugs = [str(_['titleSlug']) for _ in accepted_problems]
    problem_map = {}
    tag_map = {}
    for problem in accepted_problems:
        slug = str(problem['titleSlug'])
        problem_info = lc_helper.get_problem_by_slug(slug)
        tags = [_['name'] for _ in problem_info['topicTags']]
        problem_name = problem['translatedTitle']
        problem_id = problem['frontendId']
        problem_map[problem_id] = {
            'name': problem_name,
            'tags': tags
        }
        for tag in tags:
            if tag not in tag_map:
                tag_map[tag] = []
            tag_map[tag].append({
                'id': problem_id,
                'name': problem_name
            })
    with open('tag_map', 'w') as f:
        f.write(json.dumps(tag_map, ensure_ascii=False))
    with open('problem_map', 'w') as f:
        f.write(json.dumps(problem_map, ensure_ascii=False))
    print(problem_map)
    # accepted_problem_ids = [str(_['frontendId']) for _ in accepted_problems]
    # for problem_id in accepted_problem_ids:
    #     slug = id_slug_map.get(problem_id)
    #     if not slug:
    #         print(problem_id)
    #     problem = lc_helper.get_problem_by_slug(slug)
    #     print(problem)

