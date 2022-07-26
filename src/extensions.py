# coding=utf-8
"""
Copyright 2019-2022 Ge Yide

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
# @File    : extensions.py
# @Project : eladmin_py_backend
# from flask.ext.cache import Cache
import datetime

import redis
from flask_debugtoolbar import DebugToolbarExtension
from flask_assets import Environment


# from manage import app

# Setup flask cache
# cache = Cache(app, config={'CACHE_TYPE': 'simple'})

class AppException(Exception):
    def __init__(self, message='接口请求异常', status=400, timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        self.message = message
        self.status = status
        self.timestamp = timestamp


class RedisClient(redis.Redis):
    def __init__(self, app=None):
        if app is not None:
            self.app = app
            super().__init__(host=app.config["CACHE_REDIS_HOST"], port=app.config["CACHE_REDIS_PORT"],
                             db=app.config["CACHE_REDIS_DB"], decode_responses=True)

    def init_app(self, app):
        self.app = app
        super().__init__(host=app.config["CACHE_REDIS_HOST"], port=app.config["CACHE_REDIS_PORT"],
                         db=app.config["CACHE_REDIS_DB"], decode_responses=True)


# init flask assets
assets_env = Environment()

debug_toolbar = DebugToolbarExtension()
