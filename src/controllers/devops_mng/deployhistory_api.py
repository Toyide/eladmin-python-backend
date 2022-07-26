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

# @Time    : 2022/8/8 12:35
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : deployhistory_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import Blueprint, request
from flask_restful import Api, Resource, marshal_with

from src.config import api_utils
from src.config.api_utils import build_params, check_auth
from src.dto_mapper import deployhistory_page_fields
from src.service.devops_service import DeployHistoryService
from src.tools import format_date, download_excel

deployhistory_app = Blueprint('deployhistory', __name__, url_prefix='/api/deployHistory')
deployhistory_api = Api(deployhistory_app)


@deployhistory_api.resource('', '/')
class DeployHistoryApi(Resource):
    @check_auth('deployHistory:list', request)
    @marshal_with(deployhistory_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return DeployHistoryService.query_all(**params_dict)

    @check_auth('deployHistory:del', request)
    def delete(self):
        ids = request.get_json()
        DeployHistoryService.delete(ids=ids)


@deployhistory_api.resource('/download')
class DownloadDeployHistory(Resource):
    @check_auth('deployHistory:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = DeployHistoryService.query_all(**params_dict)
        contents = []
        for d in pagination.items:
            data = OrderedDict()
            data["部署编号"] = d.deploy_id
            data["应用名称"] = d.app_name
            data["部署IP"] = d.ip
            data["部署时间"] = format_date(d.deploy_date) if d.deploy_date else ""
            data["部署人员"] = d.deploy_user
            contents.append(data)
        return download_excel(contents)
