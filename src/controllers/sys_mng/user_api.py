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

# @Time    : 2022/6/13 13:43
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : user_api.py
# @Project : eladmin_py_backend

import json
import os
from collections import OrderedDict
from io import SEEK_END

import bcrypt
from flask import request, Blueprint, session
from flask_restful import Api, marshal_with, Resource, inputs
from flask_restful.reqparse import RequestParser
from werkzeug.utils import secure_filename

from src.config import ServerConfig, api_utils
from src.config.api_utils import build_params, oper_log, check_auth, datetime_parse
from src.dto_mapper import user_page_fields, user_edit_fields
from src.extensions import AppException
from src.models import redis_client
from src.schema import UserSchema
from src.service.sys_service import UserService, DataService, DeptService, RoleService
from src.tools import decrypt_by_private_key, check_password, download_excel, format_date

user_app = Blueprint('users', __name__, url_prefix='/api/users')
user_api = Api(user_app)


def phone_type(value):
    if value is None:
        return value
    elif isinstance(value, int):
        return inputs.regex(r'^1[3|4|5|7|8|9][0-9]\d{8}$')(str(value))
    return inputs.regex(r'^1[3|4|5|7|8|9][0-9]\d{8}$')(value)


parser = RequestParser()
parser.add_argument('id', location='json', type=int, required=True)
parser.add_argument('username', location='json', type=str, trim=True, required=True)
parser.add_argument('nickName', location='json', type=str, trim=True, required=True)
parser.add_argument('gender', location='json', type=str, choices=('男', '女'),
                    help='无效的选项: {error_msg}')
parser.add_argument('email', location='json', type=inputs.regex(
    r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'),
                    trim=True, required=True, help='格式错误: {error_msg}')
parser.add_argument('enabled', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=True)
parser.add_argument('phone', location='json', type=phone_type, trim=True,
                    help='格式错误: {error_msg}')
parser.add_argument('createBy', location='json', type=str, trim=True)
parser.add_argument('updatedBy', location='json', type=str, trim=True)
parser.add_argument('createTime', location='json', type=datetime_parse, trim=True)
parser.add_argument('updateTime', location='json', type=datetime_parse, trim=True)
parser.add_argument('deptId', location='json', type=int)
parser.add_argument('avatarName', location='json', type=str, trim=True)
parser.add_argument('avatarPath', location='json', type=str, trim=True)
parser.add_argument('pwdResetTime', location='json', type=datetime_parse, trim=True)
parser.add_argument('roles', location='json', type=list)
parser.add_argument('jobs', location='json', type=list)
parser.add_argument('dept', location='json', type=dict)
roles_parser = RequestParser()
roles_parser.add_argument('id', location='roles', type=int)
jobs_parser = RequestParser()
jobs_parser.add_argument('id', location='jobs', type=int)
dept_parser = RequestParser()
dept_parser.add_argument('id', location='dept', type=int)
dept_parser.add_argument('name', location='dept', type=str, trim=True)


@user_api.resource('', '/')
class UserAPI(Resource):
    @oper_log('查询用户', request)
    @check_auth('user:list', request)
    @marshal_with(user_page_fields)
    def get(self):
        '''
        通过token获取其信息
        获取redis缓存中此人的记录,比之前项目用数据库暂存token的方式更合理.
        Example:
        {'id': 1, 'username': 'admin', 'nickName': '管理员', 'dept': '研发部',
         'browser': 'chrome(103.0.0.0)/macos', 'ip': '127.0.0.1', 'address': ' 本机地址',
         'key': 'eyJhbGciOiJIUzI1NiIsImlhdCI6MTY1ODQ1MTIxMywiZXhwIjoxNjU4NDU0ODEzfQ.eyJpZCI6ImFkbWluIn0.WL945Yprg6RIAqP1b1ItE-3g4We8zJ8ScWvIOQpA4as', 
         'loginTime': '2022-07-22 10:09:12', 'roles': ['admin']}
        '''
        token = request.headers.environ.get('HTTP_AUTHORIZATION')
        key = f"{ServerConfig.online_key}{token[7:]}"
        data = json.loads(redis_client.get(key))


        # data = session["user"]
        user = UserService.find_by_id(user_id=data['id'])
        data_scopes = DataService.get_dept_ids(user=user)
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        dept_id = params_dict.get("deptId")
        dept_ids = []
        if dept_id:
            dept_ids.append(int(dept_id))
            dept_ids.extend(DeptService.get_dept_children(dept_list=DeptService.find_by_pid(dept_id=dept_id)))
            # dept_ids 不为空并且数据权限不为空则取交集
            # if dept_ids and data_scopes:
            #     params_dict["deptId"] = list(set(dept_ids).intersection(set(data_scopes)))
            # else:
            #     params_dict["deptId"] = list(set(dept_ids + data_scopes))
            params_dict["deptId"] = list(set(dept_ids + data_scopes))
        pagination = UserService.query_all(**params_dict)
        
        all_depts = dict((x.dept_id, x) for x in DeptService.query_all_depts())
        for u in pagination.items:
            setattr(u, 'user_dept', all_depts.get(u.dept_id))
        return pagination

    @oper_log('修改用户', request)
    @check_auth('user:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        data = session["user"]
        schema = UserSchema()
        params = request.get_json()
        params["phone"] = str(params["phone"])
        curr_user = schema.load(params, unknown="exclude")
        curr_user.update_by = data["username"]
        # edit_user = UserService.find_by_id(user_id=curr_user.user_id)
        UserService.check_level(data["id"], curr_user.roles.all())
        user = UserService.update(curr_user=curr_user)
        UserService.refresh_roles(user=user)
        return None, 204

    @oper_log('新增用户', request)
    @check_auth('user:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        params["phone"] = str(params["phone"])
        schema = UserSchema()
        curr_user = schema.load(params, unknown="exclude")
        data = session["user"]
        curr_user.create_by = data["username"]
        curr_user.password = bcrypt.hashpw(ServerConfig.default_password, bcrypt.gensalt()).decode()
        UserService.create(curr_user=curr_user)

    @oper_log('删除用户', request)
    @check_auth('user:del', request)
    def delete(self):
        ids = request.get_json()
        UserService.delete(ids=ids)


@user_api.resource('/updatePass/')
class UpdatePass(Resource):
    @oper_log('修改密码', request)
    def post(self):
        params = request.get_json()
        old_pass = decrypt_by_private_key(ServerConfig.rsa_private_key, params["oldPass"])
        new_pass = decrypt_by_private_key(ServerConfig.rsa_private_key, params["newPass"])
        data = session["user"]
        user = UserService.find_by_name(data["username"])
        if not check_password(old_pass, user.password.encode("utf-8")):
            raise AppException("修改失败，旧密码错误!")
        if check_password(new_pass, user.password.encode("utf-8")):
            raise AppException("新密码不能与旧密码相同!")
        UserService.update_pass(user, bcrypt.hashpw(new_pass, bcrypt.gensalt()).decode())


@user_api.resource('/updateAvatar')
class UpdateAvatar(Resource):
    @oper_log('修改头像', request)
    def post(self):
        # data = session["user"] # 上传文件session丢失，前端配置问题
        token = request.headers.environ.get('HTTP_AUTHORIZATION')
        key = f"{ServerConfig.online_key}{token[7:]}"
        data = json.loads(redis_client.get(key))
        file = request.files["avatar"]
        if file.filename:
            file_name = secure_filename(file.filename)
            file.seek(0, SEEK_END)
            size = file.tell()
            if size > ServerConfig.avatar_max_size * api_utils.MB:
                raise AppException("文件超出规定大小！")
            file.seek(0, os.SEEK_SET)
            file_path = os.path.join(ServerConfig.avatar, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            file.save(file_path)
            UserService.update_avatar(user_id=data["id"], file_path=file_path)
            return json.dumps({"avatar": os.path.basename(file_path)}, ensure_ascii=False)


@user_api.resource('/updateEmail/<code>')
class UpdateEmail(Resource):
    @oper_log('修改邮箱', request)
    def post(self, code):
        pass_encode = request.json["password"]
        email = request.json["email"]
        password = decrypt_by_private_key(ServerConfig.rsa_private_key, pass_encode)
        data = session["user"]
        user = UserService.find_by_id(user_id=data["id"])
        if not check_password(password, user.password.encode("utf-8")):
            raise AppException("密码错误!")
        key = f'{ServerConfig.email_reset_email_prefix}{email}'
        old_code = redis_client.get(key)
        if not old_code or old_code.lower() != code.lower():
            raise AppException("无效验证码!")
        redis_client.delete(key)
        UserService.update_email(user_id=data["id"], email=email)


@user_api.resource('/center')
class UserCenter(Resource):
    @oper_log('修改用户：个人中心', request)
    def put(self):
        parser_center = RequestParser()
        try:
            parser_center.add_argument('id', location='json', type=int, trim=True, required=True)
            parser_center.add_argument('nickName', location='json', type=str, trim=True, required=True)
            parser_center.add_argument('gender', location='json', type=str, choices=('男', '女'),
                                       help='无效的选项: {error_msg}')
            parser_center.add_argument('phone', location='json', type=phone_type, trim=True,
                                       help='格式错误: {error_msg}')
            parser_center.parse_args()
            params = request.get_json()
            user = session["user"]
            if user["id"] != params["id"]:
                raise AppException("不能修改他人资料!")
            UserService.update_center(params)
        except Exception as e:
            raise AppException(str(e))


@user_api.resource('/updateStatus')
class UserStatus(Resource):
    @oper_log('修改用户', request)
    @check_auth('user:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        data = session["user"]
        params = request.get_json()
        curr_user = UserService.find_by_id(user_id=params["id"])
        UserService.check_level(data["id"], curr_user.roles.all())
        curr_user.update_by = data["username"]
        user = UserService.update_status(curr_user=curr_user, enabled=params["enabled"])
        UserService.refresh_roles(user=user)
        return None, 204


@user_api.resource('/download')
class DownloadUsers(Resource):
    @oper_log('导出用户数据', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = UserService.query_all(**params_dict)
        contents = []
        for user in pagination.items:
            data = OrderedDict()
            data["用户名"] = user.username
            data["角色"] = ",".join([r.name for r in user.roles])
            data["部门"] = user.dept.name
            data["岗位"] = ",".join([job.name for job in user.jobs])
            data["邮箱"] = user.email
            data["状态"] = "启用" if user.enabled else "禁用"
            data["手机号码"] = str(user.phone)
            data["修改密码的时间"] = format_date(user.pwd_reset_time) if user.pwd_reset_time else ""
            data["创建日期"] = format_date(user.create_time) if user.create_time else ""
            contents.append(data)

        return download_excel(contents)


@user_api.resource('/<int:_id>')
class GetUserById(Resource):
    @oper_log('根据ID查询用户', request)
    @check_auth('user:list', request)
    @marshal_with(user_edit_fields)
    def get(self, _id):
        user = UserService.find_by_id(user_id=_id)
        return user
