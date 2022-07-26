#! ../env/bin/python
# -*- coding: utf-8 -*-
import importlib
import inspect
import os
import sys

from flasgger import Swagger
from flask import Flask
from flask_restful import Api
from flask_restful.utils import cors
from flask_session import Session
from flask_wtf import CsrfProtect
from itsdangerous import TimedJSONWebSignatureSerializer

from src.config import ServerConfig
from src.extensions import (
    # cache,
    assets_env,
    debug_toolbar,
)
from src.models import db, redis_client
from src.quartz_utils.quartz_manage import scheduler

csrf = CsrfProtect()
api = Api()
# cache = Cache()
secret_key = None


def create_token(user):
    """
    生成token
    :param user:用户id
    :return: token
    """
    # secret_key内部的私钥, expires_in有效期(秒)
    global secret_key
    serializer = TimedJSONWebSignatureSerializer(secret_key, expires_in=ServerConfig.token_validity_in_seconds)
    # 接收用户id转换与编码
    token = serializer.dumps({"id": user}).decode("ascii")
    return token


def create_app(object_name):
    """
    An flask application factory, as explained here:
    http://flask.pocoo.org/docs/patterns/appfactories/

    Arguments:
        object_name: the python path of the config object,
                     e.g. src.settings.ProdConfig

        env: The name of the current environment, e.g. prod or dev
    """

    if not os.path.exists(ServerConfig.upload_dir):
        os.makedirs(ServerConfig.upload_dir)

    app = Flask(__name__)

    app.config.from_object(object_name)
    # 返回json格式转换
    # app.json_encoder = JSONEncoder
    app.jinja_env.auto_reload = True
    global secret_key
    secret_key = app.config['SECRET_KEY']

    Session(app)

    # flask-restful
    api.init_app(app)
    api.decorators = [cors.crossdomain(origin='*', headers={'Access-Control-Allow-Origin': '*',
                                                            'Access-Control-Allow-Methods': 'HEAD, OPTIONS, GET, POST, DELETE, PUT',
                                                            'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                                                            'Access-Control-Allow-Credentials': 'true',
                                                            })]

    # initialize the debug tool bar
    debug_toolbar.init_app(app)

    # 开启csrf保护
    # csrf.init_app(app)

    # initialize SQLAlchemy
    db.init_app(app)

    scheduler.init_app(app)
    scheduler.start()

    # redis
    # redis_client.init_app(app, config=app.config)
    # global cache
    # cache.init_app(app)
    redis_client.init_app(app)

    if "SWAGGER_CONFIG" in app.config:
        Swagger(app, config=app.config["SWAGGER_CONFIG"])

    # Import and register the different asset bundles
    # assets_env.init_app(app)
    # assets_loader = PythonAssetsLoader(assets)
    # for name, bundle in assets_loader.load_bundles().items():
    #     assets_env.register(name, bundle)

    # register all blueprints and api(s) 通过walkthrough的形式遍历所有controllers文件夹下的_api.py文件
    controller_path = os.path.join(os.path.dirname(__file__), 'controllers')
    for root, dirs, files in os.walk(controller_path):
        sys.path.insert(0, root)
        for name in files:
            f = os.path.join(root, name)
            if not f.endswith('_api.py'):
                continue
            app_name = name.rsplit('_', 1)[0] + '_app'
            module = inspect.getmodulename(f)
            app.register_blueprint(getattr(importlib.import_module(module), app_name))
            if app_name == 'main_app':
                app.register_blueprint(getattr(importlib.import_module(module), "file_app"))
        sys.path.remove(root)

    return app
