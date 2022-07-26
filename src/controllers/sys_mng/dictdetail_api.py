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

# @Time    : 2022/6/12 21:43
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : dictdetail_api.py
# @Project : eladmin_py_backend

from flask import Blueprint, request, session
from flask_restful import Api, marshal_with, Resource
from flask_restful.reqparse import RequestParser

from src.config.api_utils import oper_log, check_auth
from src.dto_mapper import dictdetail_page_fields, dict_detail_fields
from src.schema import DictDetailSchema
from src.service.sys_service import DictDetailService

dictdetail_app = Blueprint('dictDetail', __name__, url_prefix='/api/dictDetail')
dictdetail_api = Api(dictdetail_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('label', location='json', type=str, trim=True, required=True)
parser.add_argument('value', location='json', type=str, trim=True, required=True)
parser.add_argument('dictSort', location='json', type=int, trim=True, required=True)


@dictdetail_api.resource('', '/')
class DictDetailAPI(Resource):
    @oper_log('查询字典详情', request)
    @marshal_with(dictdetail_page_fields)
    def get(self):
        return DictDetailService.query_all(**request.args)

    @oper_log('修改字典详情', request)
    @check_auth('dict:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        schema = DictDetailSchema()
        user = session["user"]
        params = request.get_json()
        curr_detail = schema.load(params, unknown="exclude")
        curr_detail.update_by = user["username"]
        DictDetailService.update(curr_detail=curr_detail)
        return None, 204

    @oper_log('新增字典详情', request)
    @check_auth('dict:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = DictDetailSchema()
        curr_detail = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_detail.dict_id = params["dict"]["id"]
        curr_detail.dict_sort = params["dictSort"]
        curr_detail.create_by = user["username"]
        DictDetailService.create(curr_detail=curr_detail)


@dictdetail_api.resource('/<int:id_>')
class DeleteDictDetail(Resource):
    @oper_log('删除字典详情', request)
    @check_auth('dict:del', request)
    def delete(self, id_):
        DictDetailService.delete(id_=id_)


@dictdetail_api.resource('/<int:_id>')
class GetDetailById(Resource):
    @oper_log('根据ID查询岗位', request)
    @check_auth('dict:list', request)
    @marshal_with(dict_detail_fields)
    def get(self, _id):
        data = DictDetailService.find_by_id(detail_id=_id)
        return data
