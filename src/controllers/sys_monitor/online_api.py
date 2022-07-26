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

# @Time    : 2022/7/19 11:27
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : online_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import Blueprint, request
from flask_restful import Api, Resource

from src.config.api_utils import build_params, check_auth
from src.service.monitor_service import OnlineUserService
from src.tools import download_excel

online_app = Blueprint('online', __name__, url_prefix='/auth/online')
online_api = Api(online_app)


@online_api.resource('', '/')
class OnlineUserAPI(Resource):
    @check_auth('', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        online_users = OnlineUserService.query_all(**params_dict)
        for k in online_users:
            k["userName"] = k["username"]
        return {
            'content': online_users,
            'totalElements': len(online_users)
        }

    @check_auth('', request)
    def delete(self):
        keys = request.get_json()
        for key in keys:
            OnlineUserService.kick_out(key=key)


@online_api.resource('/download')
class DownloadOnlineUsers(Resource):
    @check_auth('', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        online_users = OnlineUserService.query_all(**params_dict)
        contents = []
        for user in online_users:
            data = OrderedDict()
            data["用户名"] = user["username"]
            data["部门"] = user["dept"]
            data["登录IP"] = user["ip"]
            data["登录地点"] = user["address"]
            data["浏览器"] = user["browser"]
            data["登录日期"] = user["loginTime"]
            contents.append(data)

        return download_excel(contents)
