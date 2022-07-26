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

# @Time    : 2022/6/12 21:58
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : dept_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with, marshal, inputs
from flask_restful.reqparse import RequestParser

from src.config.api_utils import build_params, oper_log, check_auth
from src.dto_mapper import dept_page_fields, dept_fields
from src.schema import DeptSchema
from src.service.sys_service import DeptService
from src.tools import download_excel, format_date

dept_app = Blueprint('dept', __name__, url_prefix='/api/dept')
dept_api = Api(dept_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('name', location='json', type=str, trim=True, required=True)
parser.add_argument('isTop', location='json', type=str, trim=True, required=False)
parser.add_argument('label', location='json', type=str, trim=True, required=False)
parser.add_argument('pid', location='json', type=int)
parser.add_argument('deptSort', location='json', type=int, required=True)
parser.add_argument('enabled', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=True)
parser.add_argument('leaf', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)


@dept_api.resource('', '/')
class DeptAPI(Resource):
    @oper_log('查询部门', request)
    @check_auth('user:list,dept:list', request)
    @marshal_with(dept_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DeptService.query_all(**params_dict)
        return pagination

    @oper_log('新增部门', request)
    @check_auth('dept:add', request)
    def post(self):
        parser_new = parser.copy()
        parser_new.remove_argument("id")
        parser_new.parse_args()
        params = request.get_json()
        user = session["user"]
        schema = DeptSchema()
        dept = schema.load(params, unknown="exclude")
        dept.sub_count = 0
        dept.create_by = user["username"]
        DeptService.create(curr_dept=dept)

    @oper_log('删除部门', request)
    @check_auth('dept:del', request)
    def delete(self):
        ids = request.get_json()
        dept_set = DeptService.get_children_by_ids(ids=ids)
        DeptService.verification(dept_set)
        DeptService.delete(ids=ids)

    @oper_log('修改部门', request)
    @check_auth('dept:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        user = session["user"]
        schema = DeptSchema()
        dept = schema.load(request.get_json(), unknown="exclude")
        dept.update_by = user["username"]
        DeptService.update(curr_dept=dept)
        return None, 204


@dept_api.resource('/superior')
class GetSuperior(Resource):
    @oper_log('查询部门', request)
    @check_auth('user:list,dept:list', request)
    def post(self):
        all_depts = DeptService.query_all_depts()
        total, trees = DeptService.build_tree(all_depts)
        return {"totalElements": total, "content": [marshal(d, dept_fields) for d in trees]}


@dept_api.resource('/download')
class DownloadDepts(Resource):
    @oper_log('导出部门数据', request)
    @check_auth('dept:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DeptService.query_all(**params_dict)
        contents = []
        for dept in pagination.items:
            data = OrderedDict()
            data["部门名称"] = dept.name
            data["部门状态"] = "启用" if dept.enabled else "停用"
            data["创建日期"] = format_date(dept.create_time) if dept.create_time else ""
            contents.append(data)

        return download_excel(contents)


@dept_api.resource('/<int:_id>')
class GetDeptById(Resource):
    @oper_log('根据ID查询部门', request)
    @check_auth('dept:list', request)
    @marshal_with(dept_fields)
    def get(self, _id):
        data = DeptService.find_by_id(dept_id=_id)
        return data
