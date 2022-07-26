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

# @Time    : 2022/8/22 15:52
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : tool_qiniu_content.py
# @Project : eladmin_py_backend
import os
from io import SEEK_END

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with
from flask_restful.reqparse import RequestParser
from qiniu import Auth, put_file, BucketManager
from werkzeug.utils import secure_filename

from src.config import api_utils, ServerConfig
from src.config.api_utils import build_params, oper_log, get_file_type
from src.dto_mapper import tool_qiniu_content_page_fields, tool_qiniu_config_fields
from src.extensions import AppException
from src.models import ToolQiniuContent
from src.schema import ToolQiniuContentSchema, ToolQiniuConfigSchema
from src.service.sys_tools_service import ToolQiniuContentService

tool_qiniu_content_app = Blueprint('tool_qiniu_content', __name__, url_prefix='/api/qiNiuContent')
tool_qiniu_content_api = Api(tool_qiniu_content_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=False)
parser.add_argument('bucket', location='json', type=str, trim=True, required=False)
parser.add_argument('name', location='json', type=str, trim=True, required=False)
parser.add_argument('size', location='json', type=str, trim=True, required=False)
parser.add_argument('type', location='json', type=str, trim=True, required=False)
parser.add_argument('url', location='json', type=str, trim=True, required=False)
parser.add_argument('suffix', location='json', type=str, trim=True, required=False)

parser_config = RequestParser()
parser_config.add_argument('id', location='json', type=int, trim=True, required=True)
parser_config.add_argument('accessKey', location='json', type=str, trim=True, required=False)
parser_config.add_argument('bucket', location='json', type=str, trim=True, required=False)
parser_config.add_argument('host', location='json', type=str, trim=True, required=False)
parser_config.add_argument('secretKey', location='json', type=str, trim=True, required=False)
parser_config.add_argument('type', location='json', type=str, trim=True, required=False)
parser_config.add_argument('zone', location='json', type=str, trim=True, required=False)


@tool_qiniu_content_api.resource('/config')
class ToolQiniuConfigAPI(Resource):
    @oper_log('更新配置', request)
    def put(self):
        parser_put = parser_config.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = ToolQiniuConfigSchema()
        curr_data = schema.load(params, unknown="exclude")
        ToolQiniuContentService.config(curr_data=curr_data)

    @oper_log('查询配置', request)
    @marshal_with(tool_qiniu_config_fields)
    def get(self):
        return ToolQiniuContentService.find()


@tool_qiniu_content_api.resource('', '/')
class ToolQiniuContentAPI(Resource):
    @oper_log('查询文件', request)
    @marshal_with(tool_qiniu_content_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return ToolQiniuContentService.query_all(**params_dict)

    @oper_log('新增文件', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = ToolQiniuContentSchema()
        curr_data = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_data.create_by = user["username"]
        ToolQiniuContentService.create(curr_data=curr_data)

    @oper_log('删除文件', request)
    def delete(self):
        ids = request.get_json()
        ToolQiniuContentService.delete(ids=ids)


@tool_qiniu_content_api.resource('/download')
class DownloadToolQiniuContents(Resource):
    @oper_log('导出文件', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = ToolQiniuContentService.query_all(**params_dict)
        return ToolQiniuContentService.download(data_list=pagination.items)


@tool_qiniu_content_api.resource('/upload')
class UploadFile(Resource):
    @oper_log('上传文件', request)
    def post(self):
        config = ToolQiniuContentService.find()
        if config is None:
            raise AppException("请先添加相应配置，再操作！")
        file = request.files['file']
        if file.filename:
            file_name = secure_filename(file.filename)
            file.seek(0, SEEK_END)
            size = file.tell()
            if size > ServerConfig.qiniu_max_size * api_utils.MB:
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

            q = Auth(ServerConfig.qiniu_access_key, ServerConfig.qiniu_secret_key)
            # 要上传的空间
            bucket_name = config.bucket
            # 上传后保存的文件名
            key = file_name
            # 生成上传 Token，可以指定过期时间等
            token = q.upload_token(bucket_name, key, 3600)
            ret, info = put_file(token, key, file_path)
            print(info)
            curr_data = ToolQiniuContentService.find_by_name(name=info["key"])
            if curr_data is None:
                curr_data = ToolQiniuContent()
                curr_data.suffix = info["key"]
                curr_data.bucket = config.bucket
                curr_data.type = config.type
                curr_data.name = info["key"]
                curr_data.url = config.host + '/' + info["key"]
                curr_data.size = file_size
                ToolQiniuContentService.create(curr_data=curr_data)
        return {"id": curr_data.content_id, "errno": 0, "data": [curr_data.url]}


@tool_qiniu_content_api.resource('/synchronize')
class SyncQiNiu(Resource):
    @oper_log('同步七牛云数据', request)
    def post(self):
        config = ToolQiniuContentService.find()
        if config is None:
            raise AppException("请先添加相应配置，再操作！")
        q = Auth(ServerConfig.qiniu_access_key, ServerConfig.qiniu_secret_key)
        bucket = BucketManager(q)
        prefix = None  # 前缀
        limit = 1000  # 列举条目
        delimiter = None  # 列举出除'/'的所有文件以及以'/'为分隔的所有前缀
        marker = None  # 标记
        ret, eof, info = bucket.list(config.bucket, prefix, marker, limit, delimiter)
        print(info)
        print(ret)
        if ret.get('items'):
            for item in ret.get('items'):
                curr_data = ToolQiniuContentService.find_by_name(name=item["key"])
                if curr_data is None:
                    curr_data = ToolQiniuContent()
                    curr_data.suffix = item["key"]
                    curr_data.bucket = config.bucket
                    curr_data.type = config.type
                    curr_data.name = item["key"]
                    curr_data.url = config.host + '/' + item["key"]
                    curr_data.size = api_utils.get_size(int(item["fsize"]))
                    ToolQiniuContentService.create(curr_data=curr_data)
