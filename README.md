# 掘金文章爬虫
 一、项目介绍

爬取掘金后端的所有分类以及每个分类下面的所有热门文章。

二、使用说明

1、此项目基于python3.7.3，使用前请确保系统安装了python3.7.3。

2、项目中使用redis作为队列，使用前确保系统安装了redis

2、使用命令 `pip3 install -r requirement.txt` 安装依赖包。

3、在项目根目录下创建conf文件夹，文件夹中创建spider.conf，并填入以下内容：

    [main]                                  # 主要配置，名称不可变
    env=local                               # 当前环境，根据此值读取不同配置

    [mysql_local]                           # 开发环境的mysql配置
    host=host                               # host：数据库地址
    port=port                               # port：数据库端口
    user=username                           # username：用户名
    pass=password                           # password：密码
    db=db_name                              # db_name：数据库名称
    
    [redis]                                 # redis配置
    host=host                               # host：redis地址
    port=port                               # port：redis端口

4、运行

执行以下命令，运行项目：

     python3 spider/main.py                 # 爬取文章
     python3 spider/post.py                 # 爬取文章内容        