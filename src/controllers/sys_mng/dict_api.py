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

# @Time    : 2022/7/5 17:36
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : dict_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import request, Blueprint, session
from flask_restful import Api, marshal_with, Resource
from flask_restful.reqparse import RequestParser

from src.config import api_utils
from src.config.api_utils import build_params, oper_log, check_auth
from src.dto_mapper import dict_page_fields, dict_fields
from src.schema import DictSchema
from src.service.sys_service import DictService
from src.tools import format_date, download_excel

dict_app = Blueprint('dict', __name__, url_prefix='/api/dict')
dict_api = Api(dict_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('name', location='json', type=str, trim=True, required=True)
parser.add_argument('description', location='json', type=str, trim=True)


@check_auth('dict:list', request)
@dict_api.resource('/all')
class AllDict(Resource):
    @oper_log('查询字典', request)
    @marshal_with(dict_fields)
    def get(self):
        return DictService.query_all().items


@dict_api.resource('', '/')
class DictAPI(Resource):
    @oper_log('查询字典', request)
    @check_auth('dict:list', request)
    @marshal_with(dict_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return DictService.query_all(**params_dict)

    @oper_log('修改字典', request)
    @check_auth('dict:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        schema = DictSchema()
        user = session["user"]
        curr_dict = schema.load(request.get_json(), unknown="exclude")
        curr_dict.update_by = user["username"]
        DictService.update(curr_dict=curr_dict)
        return None, 204

    @oper_log('新增字典', request)
    @check_auth('dict:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = DictSchema()
        curr_dict = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_dict.create_by = user["username"]
        DictService.create(curr_dict=curr_dict)

    @oper_log('删除字典', request)
    @check_auth('dict:del', request)
    def delete(self):
        ids = request.get_json()
        DictService.delete(ids=ids)


@dict_api.resource('/download')
class DownloadDicts(Resource):
    @oper_log('导出字典数据', request)
    @check_auth('dict:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DictService.query_all(**params_dict)
        contents = []
        for d in pagination.items:
            if d.details:
                for dt in d.details:
                    data = OrderedDict()
                    data["字典名称"] = d.name
                    data["字典描述"] = d.description
                    data["字典标签"] = dt.label
                    data["字典值"] = dt.value
                    data["创建日期"] = format_date(dt.create_time) if dt.create_time else ""
                    contents.append(data)
            else:
                data = OrderedDict()
                data["字典名称"] = d.name
                data["字典描述"] = d.description
                data["字典标签"] = ""
                data["字典值"] = ""
                data["创建日期"] = format_date(d.create_time) if d.create_time else ""
                contents.append(data)
        return download_excel(contents)


@dict_api.resource('/<int:_id>')
class GetDictById(Resource):
    @oper_log('根据ID查询字典', request)
    @check_auth('dict:list', request)
    @marshal_with(dict_fields)
    def get(self, _id):
        data = DictService.find_by_id(dict_id=_id)
        return data
