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
# @File    : main.py
# @Project : eladmin_py_backend
import datetime
import json
import re
import traceback

from flask import Blueprint, jsonify, request
from marshmallow.exceptions import MarshmallowError

from src import csrf, redis_client
from src.config import ServerConfig
from src.extensions import AppException

main_app = Blueprint('main', __name__, static_folder=ServerConfig.avatar)
file_app = Blueprint('file', __name__, static_folder=ServerConfig.upload_dir)


@main_app.before_app_request
def check_csrf():
    # if not is_oauth(request):
    if request.path.endswith('/druid'):
        return "DB监控可使用HAProxy等代理工具的管理功能"
    static_paths = [".html$", "/favicon.ico$", ".css$", ".js$", "(/webSocket/)+", "/swagger-ui.html$",
                    "(/swagger-resources/)+", "(/webjars/)+", "(/apidocs)+",
                    "(/api-docs)+", "(/avatar/)+", "(/file/)+", "(/druid/)+", "(/code)", "(/auth/login)"]
    if any([re.findall(x, request.path) for x in static_paths]):
        return
    token = request.headers.environ.get('HTTP_AUTHORIZATION')
    if token:
        key = f"{ServerConfig.online_key}{token[7:]}"
        # token续期
        user = None
        if redis_client.exists(key):
            user = json.loads(redis_client.get(key))
        if user is None:
            raise AppException("登录已过期，请重新登录！", status=401)
        else:
            login_time = datetime.datetime.strptime(user["loginTime"], '%Y-%m-%d %H:%M:%S')
            # 距离token过期剩下不足ServerConfig.detect(秒)
            if datetime.datetime.now() - login_time >= datetime.timedelta(
                    seconds=ServerConfig.token_validity_in_seconds - ServerConfig.detect):
                user["loginTime"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # redis_client.set(key, user, timeout=ServerConfig.renew)
                redis_client.set(key, json.dumps(user, ensure_ascii=False))
                redis_client.expire(key, ServerConfig.renew)
            elif datetime.datetime.now() - login_time >= datetime.timedelta(
                    seconds=ServerConfig.token_validity_in_seconds):
                raise AppException("登录已过期，请重新登录！", status=401)
        return
    print(f'{request.path} is protected!')
    # csrf.protect()


@csrf.error_handler
def csrf_error(reason):
    return f"Error:{reason}", 400


# @main_app.errorhandler(404)  # 捕捉当前蓝图下所有404
@main_app.app_errorhandler(404)  # 捕捉的全局所有404
def error_404(error):
    response = dict(status=404, message="404 Not Found",
                    timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return jsonify(response), 404


@main_app.app_errorhandler(Exception)
def error_all(error):
    msg = f"警告:{str(error)}"
    status = error.status if hasattr(error, "status") else 400
    traceback.print_exc()
    if isinstance(error, MarshmallowError):
        msg = "".join([k + ":" + "".join(v) for k, v in error.messages.items()])
    response = dict(status=status, message=msg, timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return jsonify(response), status


@main_app.app_errorhandler(AppException)
def error_app(error):
    response = dict(status=error.status, message=error.message, timestamp=error.timestamp)
    return jsonify(response), 400


@main_app.after_app_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response
