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

# @Time    : 2022/6/13 18:16
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : role_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import request, Blueprint, session
from flask_restful import Resource, marshal_with, Api, marshal
from flask_restful.reqparse import RequestParser

from src.config import api_utils
from src.config.api_utils import build_params, oper_log, check_auth
from src.dto_mapper import role_page_fields, role_edit_fields
from src.schema import RoleSchema
from src.service.sys_service import RoleService
from src.tools import format_date, download_excel

role_app = Blueprint('role', __name__, url_prefix='/api/roles')
role_api = Api(role_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('name', location='json', type=str, trim=True, required=True)
parser.add_argument('level', location='json', type=int, trim=True, required=True)
parser.add_argument('description', location='json', type=str, trim=True, required=False)
parser.add_argument('dataScope', location='json', type=str, choices=('全部', '本级', '自定义'),
                    help='无效的选项: {error_msg}')


@role_api.resource('', '/')
class RoleAPI(Resource):
    @oper_log('查询角色', request)
    @check_auth('roles:list', request)
    @marshal_with(role_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return RoleService.query_all(**params_dict)

    @oper_log('新增角色', request)
    @check_auth('roles:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = RoleSchema()
        curr_role = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_role.create_by = user["username"]
        RoleService.create(curr_role=curr_role)

    @oper_log('修改角色', request)
    @check_auth('roles:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = RoleSchema()
        curr_role = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_role.update_by = user["username"]
        RoleService.update(curr_role=curr_role)

    @oper_log('删除角色', request)
    @check_auth('roles:del', request)
    def delete(self):
        user = session["user"]
        ids = request.get_json()
        for _id in ids:
            role = RoleService.find_by_id(role_id=_id)
            RoleService.get_levels(user_id=user["id"], level=role.level)

        RoleService.verification(ids=ids)
        RoleService.delete(ids=ids)


@role_api.resource('/menu')
class UpdateMenu(Resource):
    @oper_log('修改角色菜单', request)
    @check_auth('roles:edit', request)
    def put(self):
        user = session["user"]
        params = request.get_json()
        role = RoleService.find_by_id(role_id=params["id"])
        RoleService.get_levels(user_id=user["id"], level=role.level)
        # 对应此角色的用户重新登录后权限将更新
        RoleService.update_menu(params=params, role=role)
        return None, 204


@role_api.resource('/all')
class GetAll(Resource):
    @oper_log('返回全部的角色', request)
    @check_auth('roles:list,user:add,user:edit', request)
    def get(self):
        roles = RoleService.query_all_roles()
        return roles


@role_api.resource('/<role_id>')
class GetRoles(Resource):
    @oper_log('获取单个role', request)
    @check_auth('roles:list', request)
    @marshal_with(role_edit_fields)
    def get(self, role_id: int):
        return RoleService.find_by_id(role_id=role_id)


@role_api.resource('/level')
class GetLevel(Resource):
    @oper_log('获取用户级别', request)
    def get(self):
        user = session["user"]
        return {"level": RoleService.get_levels(user_id=user["id"])}


@role_api.resource('/download')
class DownloadRoles(Resource):
    @oper_log('导出角色数据', request)
    @check_auth('roles:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = RoleService.query_all(**params_dict)
        contents = []
        for role in pagination.items:
            data = OrderedDict()
            data["角色名称"] = role.name
            data["角色级别"] = role.level
            data["描述"] = role.description
            data["创建日期"] = format_date(role.create_time) if role.create_time else ""
            contents.append(data)

        return download_excel(contents)


@role_api.resource('/<int:_id>')
class GetRoleById(Resource):
    @oper_log('根据ID查询角色', request)
    @check_auth('roles:list', request)
    @marshal_with(role_edit_fields)
    def get(self, _id):
        role = RoleService.find_by_id(role_id=_id)
        return role
