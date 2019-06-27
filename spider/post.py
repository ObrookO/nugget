# 爬取文章详情
import requests
import os
import sys
from model.model import Model
from bs4 import BeautifulSoup
from pymysql import escape_string
import json
import re
import configparser
import redis

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path)


class PostSpider:
    def __init__(self):
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

        # 连接数据库
        self.model = Model(db['host'], db['port'], db['user'], db['password'], db['db'])
        self.redis = redis.Redis()
        self.get_article()

    def get_article(self):
        article = self.redis.rpop('article')
        if article is not None:
            article = json.loads(article)
            content = self.get_detail(article['url'])

            # 如果获取不到内容，则在数据库中删除此文章
            if content is not None:
                sql = '''
                update nugget_articles set content = '%s' where out_id = '%s'
                ''' % (escape_string(content), article['id'])
            else:
                sql = '''
                delete from nugget_articles where out_id = '%s'
                ''' % article['id']

            res = self.model.commit(sql)
            if res:
                print('获取 ' + article['url'] + ' 内容成功')

            self.get_article()

    def get_detail(self, url):
        headers = {
            "X-Agent": "Juejin/Web"
        }

        r = requests.get(url, headers=headers)
        s = BeautifulSoup(r.text, 'lxml')
        article_content = s.find(class_='article-content')
        if article_content is not None:
            article_content = s.find(class_='article-content').prettify()
            article_content = re.sub(r'(<img.*?)data-src=(.*?)>', self.get_content, article_content)

        return article_content

    # 使用src替换文章中img中的data-src
    def get_content(self, matched):
        return matched.groups()[0] + 'src=' + matched.groups()[1]


if __name__ == '__main__':
    while True:
        post = PostSpider()
