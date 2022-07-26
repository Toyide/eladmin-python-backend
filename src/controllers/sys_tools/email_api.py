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

# @Time    : 2022/8/15 18:28
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : emai_api.py
# @Project : eladmin_py_backend

from flask import Blueprint, request
from flask_restful import Api, Resource, marshal_with
from flask_restful.reqparse import RequestParser

from src.config.api_utils import oper_log
from src.dto_mapper import tool_email_config_fields
from src.schema import ToolEmailConfigSchema
from src.service.sys_tools_service import ToolEmailConfigService

email_app = Blueprint('toolEmailConfig', __name__, url_prefix='/api/email')
email_api = Api(email_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=False)
parser.add_argument('fromUser', location='json', type=str, trim=True, required=True)
parser.add_argument('host', location='json', type=str, trim=True, required=True)
parser.add_argument('pass', location='json', type=str, trim=True, required=True)
parser.add_argument('port', location='json', type=str, trim=True, required=True)
parser.add_argument('user', location='json', type=str, trim=True, required=True)


@email_api.resource('', '/')
class ToolEmailConfigAPI(Resource):
    @marshal_with(tool_email_config_fields)
    def get(self):
        return ToolEmailConfigService.find()

    @oper_log("配置邮件", request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = ToolEmailConfigSchema()
        curr_config = schema.load(params, unknown="exclude")
        curr_config.password = params["pass"]
        ToolEmailConfigService.update(curr_config=curr_config)

    @oper_log("发送邮件", request)
    def post(self):
        params = request.get_json()
        email_info = {"receivers": params["tos"], "subject": params["subject"], "content": params["content"]}
        ToolEmailConfigService.send(email_info)
