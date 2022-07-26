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

# @Time    : 2022/5/20 20:24
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : auth_controller.py
# @Project : eladmin_py_backend
import datetime
import json
import uuid

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal

from src import redis_client, create_token
from src.config import ServerConfig
from src.config.api_utils import get_addr
from src.dto_mapper import user_edit_fields
from src.extensions import AppException
from src.schema import OnlineUser, UserSchema, JwtUser
from src.service.monitor_service import OnlineUserService
from src.service.sys_service import DataService, RoleService, UserService
from src.tools import verify_image, decrypt_by_private_key, check_password

auth_app = Blueprint('auth', __name__, url_prefix='/auth')
auth_api = Api(auth_app)


# @csrf.exempt
@auth_api.resource('/code')
class GetCode(Resource):
    def get(self):
        key = request.args.get("uuid")
        code, img_str = verify_image()
        key = key if key else str(uuid.uuid1())
        rs = {'uuid': key, 'img': img_str}
        redis_client.set(key, code)
        redis_client.expire(key, datetime.timedelta(minutes=ServerConfig.login_code_expiration))
        return rs


@auth_api.resource('/info')
class GetUserInfo(Resource):
    def get(self):
        user = session.get('user')
        if user is None:
            raise AppException("未登录或登录已过期，请重新登录！")
        curr_user = UserService.find_by_id(user_id=user["id"])
        user_dict = marshal(curr_user, user_edit_fields)
        return {'user': user_dict, 'dataScopes': [curr_user.dept_id],
                "roles": RoleService.map_to_granted_authorities(user=curr_user)}


# @csrf.exempt
@auth_api.resource('/login')
class Login(Resource):
    def post(self):
        data = request.get_json()
        if "uuid" not in data:
            raise AppException("验证码不存在或已过期")
        code_id = data['uuid']
        code = redis_client.get(code_id)
        if not code:
            raise AppException("验证码不存在或已过期")
        if code.lower() != data['code'].lower():
            redis_client.delete(code_id)
            raise AppException("验证码错误")
        redis_client.delete(code_id)

        # 生成令牌
        token = create_token(data["username"])
        # 获取用户信息
        user = UserService.find_by_name(data["username"])
        if user is None:
            raise AppException("用户名或密码错误，请重新输入!")

        # 密码解密
        password = decrypt_by_private_key(ServerConfig.rsa_private_key, data["password"])
        if not check_password(password, user.password.encode("utf-8")):
            raise AppException("用户名或密码错误，请重新输入!")

        browser = f'{request.user_agent.browser}({request.user_agent.version})/{request.user_agent.platform}'
        address = get_addr(request.remote_addr)
        roles = RoleService.map_to_granted_authorities(user=user)
        online_schema = OnlineUser(id=user.user_id, username=user.username, nick_name=user.nick_name,
                                   dept=user.dept.name, browser=browser, ip=request.remote_addr, address=address,
                                   key=token, roles=roles)
        online_user = online_schema.to_dict()
        # 保存在线信息
        # redis_client.set(f"{ServerConfig.online_key}{token}", online_user,
        #                  timeout=ServerConfig.token_validity_in_seconds)
        redis_client.set(f"{ServerConfig.online_key}{token}", json.dumps(online_user, ensure_ascii=False))
        redis_client.expire(f"{ServerConfig.online_key}{token}", ServerConfig.token_validity_in_seconds)
        user_schema = UserSchema()
        user_dict = user_schema.dump(user)
        session["user"] = online_user
        jwt_user = JwtUser(user=user_dict, dataScopes=DataService.get_dept_ids(user=user), roles=roles)
        rs = {'token': f'{ServerConfig.token_start_with} {token}', "user": jwt_user.to_dict()}
        OnlineUserService.check_online_user(username=user.username, igore_token=token)
        return rs


@auth_api.resource('/logout')
class Logout(Resource):
    def delete(self):
        # session.pop('user', None)
        token = request.headers.environ.get("HTTP_AUTHORIZATION")
        if token:
            redis_client.delete(f"{ServerConfig.online_key}{token}")
        return None, 200
