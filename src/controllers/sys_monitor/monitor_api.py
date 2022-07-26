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

# @Time    : 2022/7/26 20:38
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : monitor_api.py
# @Project : eladmin_py_backend
from flask import Blueprint, request
from flask_restful import Api, Resource

from src.config.api_utils import check_auth
from src.service.monitor_service import MonitorService

monitor_app = Blueprint('monitor', __name__, url_prefix='/api/monitor')
monitor_api = Api(monitor_app)


@monitor_api.resource('', '/')
class MonitorApi(Resource):
    @check_auth('monitor:list', request)
    def get(self):
        return MonitorService.get_servers()
