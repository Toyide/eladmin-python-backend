# coding=utf-8
"""
Copyright 2019-2020 Ge Yide

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# @Time    : 2022/5/15 20:49
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : settings.py
# @Project : eladmin_py_backend
import os
from datetime import timedelta

import redis

from src.config import ServerConfig


class Config(object):
    TEMPLATES_AUTO_RELOAD = True
    JSON_AS_ASCII = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    ASSETS_DEBUG = True

    LOG_LEVEL = "DEBUG"
    # 配置7天有效
    SECRET_KEY = os.urandom(24)  # 随机产生24位的字符串作为SECRET_KEY
    # 配置7天有效
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=ServerConfig.token_validity_in_seconds)

    MYSQL_DATABASE = 'your_db_name'
    MYSQL_HOST = 'your_db_host'
    MYSQL_PORT = 'your_db_port'
    MYSQL_USERNAME = 'your_db_username'
    MYSQL_PASSWORD = 'your_db_password'

    # 本地mysql
    # MYSQL_HOST = 'localhost'
    # MYSQL_PORT = '3306'
    # MYSQL_DATABASE = 'exam'
    # MYSQL_USERNAME = 'root'
    # MYSQL_PASSWORD = 'x5'

    # 数据库链接配置: 数据类型://登录账号:登录密码@数据库主机IP:数据库访问端口/数据库名称
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset=utf8".format(username=MYSQL_USERNAME,
                                                                                                             password=MYSQL_PASSWORD,
                                                                                                             host=MYSQL_HOST,
                                                                                                             port=MYSQL_PORT,
                                                                                                             db=MYSQL_DATABASE)
    # SQLAlchemy 连接池，默认5
    SQLALCHEMY_POOL_SIZE = 3
    # SQLAlchemy 连接超时时间，默认10
    SQLALCHEMY_POOL_TIMEOUT = 10
    # 设置mysql的错误跟踪信息显示
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # 多少秒后自动回收连接。对MySQL是必要的， 它默认移除闲置8+小时的连接。如果使用MySQL，Flask-SQLALchemy自动设定这个值为2小时
    # 需小于MySQL的wait_timeout配置
    SQLALCHEMY_POOL_RECYCLE = 2 * 60 * 60
    # 控制在连接池达到最大值后可以创建的连接数。当这些额外的 连接回收到连接池后将会被断开和抛弃
    SQLALCHEMY_MAX_OVERFLOW = 10
    # 打印每次模型操作对应的SQL语句
    SQLALCHEMY_ECHO = False

    CACHE_TYPE = 'redis'  # 使用redis作为缓存
    # CACHE_KEY_PREFIX  # 设置cache_key的前缀
    CACHE_REDIS_HOST = '127.0.0.1'  # redis地址
    CACHE_REDIS_PORT = 6379  # redis端口
    # CACHE_REDIS_PASSWORD=  # redis密码
    CACHE_REDIS_DB = 0  # 使用哪个数据库
    # CACHE_DEFAULT_TIMEOUT = 60  # 默认过期/超时时间，单位为秒
    CACHE_KEY_PREFIX = ""  # 缓存前缀

    # SESSION_TYPE 包括：redis mongodb memcached sqlchemy
    SESSION_TYPE = "redis"
    # 如果设置session的生命周期是否是会话期, 为True，则关闭浏览器session就失效
    SESSION_PERMANENT = False
    # 是否对发送到浏览器上session的cookie值进行加密
    SESSION_USE_SIGNER = False
    # 保存到redis的session数的名称前缀
    SESSION_KEY_PREFIX = "session:"
    # session保存数据到redis时启用的链接对象
    SESSION_REDIS = redis.Redis(
        host=CACHE_REDIS_HOST, port=CACHE_REDIS_PORT, db=CACHE_REDIS_DB)

    # 图像路径
    CUSTOM_STATIC_PATH = ServerConfig.avatar


class ProdConfig(Config):
    ENV = 'prod'
    ServerConfig.generator_enabled = False


class DevConfig(Config):
    ENV = 'dev'
    DEBUG = True
    ServerConfig.generator_enabled = True
    SWAGGER_CONFIG = {
        "headers": [
        ],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        # "static_folder": "static",  # must be set by user
        "swagger_ui": True,
        "specs_route": "/swagger-ui.html/"
    }


class TestConfig(Config):
    ENV = 'test'
    DEBUG = True
    WTF_CSRF_ENABLED = False
    ServerConfig.generator_enabled = True
