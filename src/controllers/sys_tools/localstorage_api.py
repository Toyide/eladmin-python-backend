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

import json
import os
from io import SEEK_END

from flask import request, session, Blueprint
from flask_restful import Resource, marshal_with, Api
from flask_restful.reqparse import RequestParser
from werkzeug.utils import secure_filename

from src.config import api_utils, ServerConfig
from src.config.api_utils import oper_log, build_params, get_file_type
from src.dto_mapper import tool_local_storage_page_fields
from src.extensions import AppException
from src.models import ToolLocalStorage, redis_client
from src.schema import ToolLocalStorageSchema
from src.service.sys_tools_service import ToolLocalStorageService

localstorage_app = Blueprint('localStorage', __name__, url_prefix='/api/localStorage')
localstorage_api = Api(localstorage_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('realName', location='json', type=str, trim=True, required=True)
parser.add_argument('name', location='json', type=str, trim=True, required=True)
parser.add_argument('suffix', location='json', type=str, trim=True, required=True)
parser.add_argument('path', location='json', type=str, trim=True, required=True)
parser.add_argument('type', location='json', type=str, trim=True, required=True)
parser.add_argument('size', location='json', type=str, trim=True, required=True)


@localstorage_api.resource('', '/')
class ToolLocalStorageAPI(Resource):
    @oper_log('查询文件', request)
    @marshal_with(tool_local_storage_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return ToolLocalStorageService.query_all(**params_dict)

    @oper_log('新增文件', request)
    def post(self):
        file = request.files['file']
        name = request.args['name']
        if file.filename:
            file_name = secure_filename(file.filename)
            file.seek(0, SEEK_END)
            size = file.tell()
            if size > ServerConfig.max_size * api_utils.MB:
                raise AppException("文件超出规定大小！")
            file_size = api_utils.get_size(size)
            file.seek(0, os.SEEK_SET)
            suffix = file_name.rsplit(".", 1)[-1] if "." in file_name else file_name
            file_type = get_file_type(suffix)
            dir_path = os.path.join(ServerConfig.upload_dir, f'{file_type}')
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            file_path = os.path.join(dir_path, f'{file_name}')
            if os.path.exists(file_path):
                os.remove(file_path)
            file.save(file_path)
            # user = session["user"]
            token = request.headers.environ.get('HTTP_AUTHORIZATION')
            key = f"{ServerConfig.online_key}{token[7:]}"
            data = json.loads(redis_client.get(key))
            name = os.path.splitext(file_name)[0] if not name else name
            curr_tool = ToolLocalStorage()
            curr_tool.name = name
            curr_tool.real_name = file_name
            curr_tool.suffix = suffix
            curr_tool.path = file_path
            curr_tool.type = file_type
            curr_tool.size = file_size
            curr_tool.create_by = data["username"]
            ToolLocalStorageService.create(curr_tool=curr_tool)

    @oper_log('修改文件', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = ToolLocalStorageSchema()
        curr_tool = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_tool.update_by = user["username"]
        ToolLocalStorageService.update(curr_tool=curr_tool)

    @oper_log('删除文件', request)
    def delete(self):
        ids = request.get_json()
        ToolLocalStorageService.delete(ids=ids)


@localstorage_api.resource('/download')
class DownloadToolLocalStorages(Resource):
    @oper_log('导出数据', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = ToolLocalStorageService.query_all(**params_dict)
        return ToolLocalStorageService.download(data_list=pagination.items)
