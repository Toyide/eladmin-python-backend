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

# @Time    : 2022/8/8 21:02
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : database_api.py
# @Project : eladmin_py_backend
import os
from collections import OrderedDict

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with
from flask_restful.reqparse import RequestParser
from werkzeug.utils import secure_filename

from src.config import api_utils, ServerConfig
from src.config.api_utils import build_params, check_auth
from src.dto_mapper import database_page_fields
from src.extensions import AppException
from src.schema import DatabaseSchema
from src.service.devops_service import DatabaseService
from src.tools import format_date, download_excel

database_app = Blueprint('database', __name__, url_prefix='/api/database')
database_api = Api(database_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=str, trim=True, required=True)
parser.add_argument('name', location='json', type=str, trim=True, required=True)
parser.add_argument('jdbcUrl', location='json', type=str, trim=True, required=True)
parser.add_argument('userName', location='json', type=str, trim=True, required=True)
parser.add_argument('pwd', location='json', type=str, trim=True, required=True)


@database_api.resource('', '/')
class DatabaseAPI(Resource):
    @check_auth('database:list', request)
    @marshal_with(database_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DatabaseService.query_all(**params_dict)
        return pagination

    @check_auth('database:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = DatabaseSchema()
        curr_db = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_db.create_by = user["username"]
        DatabaseService.create(curr_db=curr_db)

    @check_auth('database:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = DatabaseSchema()
        curr_db = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_db.update_by = user["username"]
        DatabaseService.update(curr_db=curr_db)

    @check_auth('database:del', request)
    def delete(self):
        ids = request.get_json()
        DatabaseService.delete(ids=ids)


@database_api.resource('/download')
class DownloadDatabase(Resource):
    @check_auth('database:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DatabaseService.query_all(**params_dict)
        contents = []
        for d in pagination.items:
            data = OrderedDict()
            data["数据库名称"] = d.name
            data["数据库连接地址"] = d.jdbc_url
            data["用户名"] = d.user_name
            data["创建日期"] = format_date(d.create_time) if d.create_time else ""
            contents.append(data)
        return download_excel(contents)


@database_api.resource('/testConnect')
class TestConnectAPI(Resource):
    @check_auth('database:testConnect', request)
    def post(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = DatabaseSchema()
        curr_db = schema.load(params, unknown="exclude")
        return DatabaseService.test_connect(curr_db=curr_db)


@database_api.resource('/upload')
class DatabaseUpload(Resource):
    @check_auth('database:add', request)
    def post(self):
        db_id = request.form["id"]
        curr_db = DatabaseService.find_by_id(db_id=db_id)
        file = request.files['file']
        if curr_db and file.filename:
            file_name = secure_filename(file.filename)
            file_path = os.path.join(ServerConfig.upload_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            file.save(file_path)
            rs = api_utils.execute_file(curr_db, file_path)
        else:
            raise AppException("Database不存在!")
        return rs
