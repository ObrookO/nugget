# 爬取文章详情
import requests
from bs4 import BeautifulSoup
from model.model import Model
from pymysql import escape_string
import pika
import json
import re
import configparser


class PostSpider:
    def __init__(self):
        # 读取配置信息
        config = configparser.ConfigParser()
        config.read('../conf/spider.conf', encoding='utf-8')
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

        # RabbitMQ相关操作
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='article')
        self.channel.queue_declare(queue='article')
        self.channel.queue_bind(queue='article', routing_key='', exchange='article')
        self.channel.basic_consume(queue='article', on_message_callback=self.get_article, auto_ack=True)
        self.channel.start_consuming()

    def get_article(self, channel, method, properties, body):
        article = json.loads(body.decode(encoding='utf-8'))
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
            print('获取' + article['url'] + '内容成功')

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
    post = PostSpider()
