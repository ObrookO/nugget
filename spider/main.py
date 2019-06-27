# 爬取后端下所有的标签，以及每个标签下的所有文章
import requests
import os
import sys

from datetime import datetime
from pymysql import escape_string
import json
import configparser
import redis
import random

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path)

from model.model import Model


class MainSpider:
    def __init__(self):
        # 接口地址
        self.dataUrl = 'https://web-api.juejin.im/query'

        # 读取配置信息
        config = configparser.ConfigParser()
        config_path = path + '/conf/spider.conf'
        config.read(config_path, encoding='utf-8')
        # 获取当前环境
        env = config.get('main', 'env')
        mysql_section = 'mysql_' + env
        db = {
            'host': config.get(mysql_section, 'host'),
            'port': int(config.get(mysql_section, 'port')),
            'user': config.get(mysql_section, 'user'),
            'password': config.get(mysql_section, 'pass'),
            'db': config.get(mysql_section, 'db')
        }

        r = {
            'host': config.get('redis', 'host'),
            'port': config.get('redis', 'port')
        }

        # 连接数据库
        self.model = Model(db['host'], db['port'], db['user'], db['password'], db['db'])
        self.redis = redis.Redis(r['host'], r['port'])

    # 获取所有的标签
    def get_tags(self):
        tags = self.model.get_all('''select * from nugget_tags''')
        if len(tags) == 0:
            headers = {
                "X-Agent": "Juejin/Web"
            }
            param = {
                "operationName": "",
                "query": "",
                "variables": {
                    "category": "5562b419e4b00c57d9b94ae2",
                    "limit": 15
                },
                "extensions": {
                    "query": {
                        "id": "801e22bdc908798e1c828ba6b71a9fd9"
                    }
                }
            }

            r = requests.post(self.dataUrl, headers=headers, json=param)
            res = json.loads(r.text)

            if 'errors' in res:
                print("获取数据失败")
                return False

            for item in res['data']['tagNav']['items']:
                info = self.model.get_one("select * from nugget_tags where out_id = '%s'" % item['tagId'])
                if info is None:
                    sql = "insert into nugget_tags (name, out_id) values ('%s', '%s')" % (item['title'], item['tagId'])
                    row = self.model.commit(sql)

                    if row == 0:
                        print('标签插入失败，标签id为：' + item['tagId'])
                    else:
                        print('标签插入成功，title为：' + item['title'])

        tags = self.model.get_all('''select * from nugget_tags''')
        return tags

    # 获取文章列表
    def get_article_lists(self, category_id, order, after=''):
        headers = {
            "X-Agent": "Juejin/Web"
        }
        params = {
            "operationName": "",
            "query": "",
            "variables": {
                "tags": [category_id],
                "category": "5562b419e4b00c57d9b94ae2",
                "first": 20,
                "after": after,
                "order": order
            },
            "extensions": {
                "query": {
                    "id": "653b587c5c7c8a00ddf67fc66f989d42"
                }
            }
        }
        proxies = {
            # 'http': 'http://223.245.34.31:65309',
            'https': 'https://218.60.8.83:3129'
        }

        r = requests.post(self.dataUrl, headers=headers, proxies=proxies, json=params)
        r.encoding = 'utf8'
        res = json.loads(r.text)

        # 文章列表
        articles = res['data']['articleFeed']['items']['edges']
        # 分页信息
        page_info = res['data']['articleFeed']['items']['pageInfo']

        # 首先处理当前页的文章，如果还有下一页，再去读取下一页的文章
        for item in articles:
            article = item['node']

            if 'juejin.im' in article['originalUrl']:
                select_sql = '''
                select * from nugget_articles where out_id = "%s"
                ''' % article['id']

                info = self.model.get_one(select_sql)
                if info is None:
                    # 拼接tag
                    tag_list = [tag['id'] for tag in article['tags']]
                    tags = ','.join(tag_list)

                    # 插入文章信息
                    insert_sql = '''
                    insert into nugget_articles (out_id, origin_url, title, category, tags, catch_at) values ('%s','%s','%s','%s','%s','%s')''' % (
                        article['id'], article['originalUrl'], escape_string(article['title']), category_id, tags, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    self.model.commit(insert_sql)

                    print('文章 ', article['id'], ' 插入成功！')
                    # 把文章id和原始url放入队列中
                    message = json.dumps({'id': article['id'], 'url': article['originalUrl']})
                    self.redis.lpush('article', message)
                    # self.channel.basic_publish(exchange=self.exchange_name, routing_key='', body=message, properties=pika.BasicProperties(delivery_mode=2))
                else:
                    print('文章 ', article['id'], ' 已存在！')

        if page_info['hasNextPage'] is True:
            self.get_article_lists(category_id, order, page_info['endCursor'])


if __name__ == '__main__':
    spider = MainSpider()
    tags = spider.get_tags()
    order = ['POPULAR', 'HOTTEST', 'MONTHLY_HOTTEST']
    for item in tags:
        spider.get_article_lists(item[2], random.choice(order))
