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

# @Time    : 2022/8/21 20:15
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : pictures_api.py
# @Project : eladmin_py_backend
import json
import os
import uuid

import requests
from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with
from flask_restful.reqparse import RequestParser
from werkzeug.utils import secure_filename

from src import redis_client
from src.config import api_utils, ServerConfig
from src.config.api_utils import build_params, oper_log, get_md5, upload_sm_ms, datetime_parse
from src.dto_mapper import tool_picture_page_fields
from src.schema import PictureSchema
from src.service.sys_tools_service import PictureService

pictures_app = Blueprint('pictures', __name__, url_prefix='/api/pictures')
pictures_api = Api(pictures_app)

parser = RequestParser()
parser.add_argument('pictureId', location='json', type=int, trim=True, required=True)
parser.add_argument('filename', location='json', type=str, trim=True, required=True)
parser.add_argument('md5code', location='json', type=str, trim=True, required=True)
parser.add_argument('size', location='json', type=str, trim=True, required=True)
parser.add_argument('url', location='json', type=str, trim=True, required=True)
parser.add_argument('deleteUrl', location='json', type=str, trim=True, required=True)
parser.add_argument('height', location='json', type=str, trim=True, required=True)
parser.add_argument('width', location='json', type=str, trim=True, required=True)
parser.add_argument('username', location='json', type=str, trim=True, required=True)
parser.add_argument('createTime', location='json', type=datetime_parse, trim=True, required=False)


@pictures_api.resource('', '/')
class PictureAPI(Resource):
    @oper_log('查询图片', request)
    @marshal_with(tool_picture_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return PictureService.query_all(**params_dict)

    @oper_log('上传图片', request)
    def post(self):
        file = request.files['file']
        if file.filename:
            file_name = secure_filename(file.filename)
            file_path = os.path.join(ServerConfig.upload_dir, f'{str(uuid.uuid1())}_{file_name}')
            if os.path.exists(file_path):
                os.remove(file_path)
            file.save(file_path)
            file_md5 = get_md5(file_path)
            picture = PictureService.find_by_md5(file_md5)
            if picture:
                return picture
            params = {"smfile": open(file_path, 'rb+')}
            result = upload_sm_ms(params)
            schema = PictureSchema()
            curr_picture = schema.load(result, unknown="exclude")
            # user = session["user"]
            token = request.headers.environ.get('HTTP_AUTHORIZATION')
            key = f"{ServerConfig.online_key}{token[7:]}"
            data = json.loads(redis_client.get(key))
            curr_picture.delete_url = result.get("delete")
            curr_picture.md5code = file_md5
            curr_picture.username = data["username"]
            PictureService.create(curr_picture=curr_picture)

    @oper_log('修改图片', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = PictureSchema()
        curr_picture = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_picture.update_by = user["username"]
        PictureService.update(curr_picture=curr_picture)

    @oper_log('删除图片', request)
    def delete(self):
        ids = request.get_json()
        PictureService.delete(ids=ids)


@pictures_api.resource('/synchronize')
class SyncPictures(Resource):
    @oper_log('同步图床数据', request)
    def post(self):
        rsp = requests.get(f'{ServerConfig.sm_ms_url}/v2/history', headers={
            'Content-Type': 'multipart/form-data',
            'Authorization': ServerConfig.sm_ms_token
        }, timeout=10)
        rs = rsp.json()
        schema = PictureSchema()
        pictures = [schema.load(d, unknown="exclude") for d in rs["data"]]
        PictureService.save(pictures=pictures)


@pictures_api.resource('/download')
class DownloadPictures(Resource):
    @oper_log('导出图片数据', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = PictureService.query_all(**params_dict)
        return PictureService.download(data_list=pagination.items)
