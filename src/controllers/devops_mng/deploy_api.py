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

# @Time    : 2022/7/19 19:42
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : deploy_api.py
# @Project : eladmin_py_backend
import json
import os
from collections import OrderedDict

from flask import Blueprint, request
from flask_restful import Api, Resource, marshal_with
from werkzeug.utils import secure_filename

from src import ServerConfig, redis_client
from src.config.api_utils import build_params, check_auth
from src.dto_mapper import deploy_page_fields
from src.service.devops_service import DeployService
from src.tools import download_excel, format_date

deploy_app = Blueprint('deploy', __name__, url_prefix='/api/deploy')
deploy_api = Api(deploy_app)


@deploy_api.resource('', '/')
class DeployAPI(Resource):
    @check_auth('deploy:list', request)
    @marshal_with(deploy_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DeployService.query_all(**params_dict)
        return pagination


@deploy_api.resource('/download')
class DownloadDeploy(Resource):
    @check_auth('deploy:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DeployService.query_all(**params_dict)
        contents = []
        for d in pagination.items:
            data = OrderedDict()
            data["应用名称"] = d.app.name
            data["服务器"] = ",".join([server.name for server in d.deploys])
            data["部署日期"] = format_date(d.create_time) if d.create_time else ""
            contents.append(data)
        return download_excel(contents)


@deploy_api.resource('/upload')
class DeployUpload(Resource):
    @check_auth('deploy:edit', request)
    def post(self):
        deploy_id = int(request.form["id"])
        file = request.files['file']
        # data = session["user"]  # 此处无法获取session
        token = request.headers.environ.get('HTTP_AUTHORIZATION')
        key = f"{ServerConfig.online_key}{token[7:]}"
        data = json.loads(redis_client.get(key))
        file_name = ""
        if file.filename:
            file_name = secure_filename(file.filename)
            file_path = os.path.join(ServerConfig.upload_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
            file.save(file_path)
            DeployService.deploy(file_save_path=file_path, deploy_id=deploy_id, username=data["username"])
        rs = {"errno": 0, "id": file_name}
        return rs
