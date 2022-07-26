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

# @Time    : 2022/7/19 19:35
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : app_api.py
# @Project : eladmin_py_backend
import datetime

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with
from flask_restful.reqparse import RequestParser

from src.config.api_utils import build_params, oper_log, check_auth
from src.dto_mapper import app_page_fields
from src.schema import AppSchema
from src.service.devops_service import AppService

app_app = Blueprint('app', __name__, url_prefix='/api/app')
app_api = Api(app_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('name', location='json', type=str, trim=True, required=True)
parser.add_argument('port', location='json', type=int, trim=True, required=True)
parser.add_argument('uploadPath', location='json', type=str, trim=True, required=True)
parser.add_argument('deployPath', location='json', type=str, trim=True, required=True)
parser.add_argument('backupPath', location='json', type=str, trim=True, required=True)
parser.add_argument('startScript', location='json', type=str, trim=True, required=True)
parser.add_argument('deployScript', location='json', type=str, trim=True, required=True)
parser.add_argument('createBy', location='json', type=str, trim=True, required=True)
parser.add_argument('updatedBy', location='json', type=str, trim=True, required=True)


@app_api.resource('', '/')
class AppAPI(Resource):
    @oper_log('查询应用', request)
    @check_auth('app:list', request)
    @marshal_with(app_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = AppService.query_all(**params_dict)
        return pagination

    @oper_log('新增应用', request)
    @check_auth('app:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = AppSchema()
        curr_app = schema.load(params, unknown="exclude")
        data = session["user"]
        curr_app.create_by = data["username"]
        AppService.create(curr_app=curr_app)

    @oper_log('修改应用', request)
    @check_auth('app:edit', request)
    def put(self):
        parser_post = parser.copy()
        parser_post.parse_args()
        params = request.get_json()
        schema = AppSchema()
        curr_app = schema.load(params, unknown="exclude")
        data = session["user"]
        curr_app.update_by = data["username"]
        AppService.update(curr_app=curr_app)

    @oper_log('删除应用', request)
    @check_auth('app:del', request)
    def delete(self):
        ids = request.get_json()
        AppService.delete(ids=ids)


@app_api.resource('/download')
class DownloadApps(Resource):
    @oper_log('导出App', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = AppService.query_all(**params_dict)
        return AppService.download(data_list=pagination.items)
