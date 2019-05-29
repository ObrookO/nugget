import pymysql


class Model:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

        self.link = self.cursor = None
        self.connect()

    # 连接数据库
    def connect(self):
        try:
            db = pymysql.connect(host=self.host, port=self.port, user=self.user, password=self.password, database=self.database)

            if db is not None:
                self.link = db
                self.cursor = db.cursor()
        except:
            raise

    # 获取所有数据
    def get_all(self, sql):
        try:
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except:
            raise

    # 获取单条数据
    def get_one(self, sql):
        try:
            self.cursor.execute(sql)
            return self.cursor.fetchone()
        except:
            raise

    # 提交sql，包括（增、删、改操作）
    def commit(self, sql):
        try:
            self.cursor.execute(sql)
            self.link.commit()

            return self.cursor.rowcount
        except:
            self.link.rollback()
            raise

    # 析构函数
    def __del__(self):
        if self.link is not None:
            self.link.close()
