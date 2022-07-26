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

# @Time    : 2022/8/15 13:39:58
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : ToolAlipayConfig.py
# @Project : eladmin_py_backend

from flasgger import swag_from
from flask import Blueprint, request
from flask_restful import Api, Resource, marshal_with
from flask_restful.reqparse import RequestParser

from src.dto_mapper import alipay_fields
from src.schema import ToolAlipayConfigSchema
from src.service.sys_tools_service import ToolAlipayConfigService

alipay_app = Blueprint('aliPay', __name__, url_prefix='/api/aliPay')
alipay_api = Api(alipay_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('appId', location='json', type=str, trim=True, required=False)
parser.add_argument('charset', location='json', type=str, trim=True, required=False)
parser.add_argument('format', location='json', type=str, trim=True, required=False)
parser.add_argument('gatewayUrl', location='json', type=str, trim=True, required=False)
parser.add_argument('notifyUrl', location='json', type=str, trim=True, required=False)
parser.add_argument('privateKey', location='json', type=str, trim=True, required=False)
parser.add_argument('publicKey', location='json', type=str, trim=True, required=False)
parser.add_argument('returnUrl', location='json', type=str, trim=True, required=False)
parser.add_argument('signType', location='json', type=str, trim=True, required=False)
parser.add_argument('sysServiceProviderId', location='json', type=str, trim=True, required=False)


@swag_from('/api/aliPay')
@alipay_api.resource('', '/')
class ToolAlipayConfigAPI(Resource):
    @marshal_with(alipay_fields)
    def get(self):
        return ToolAlipayConfigService.find()

    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = ToolAlipayConfigSchema()
        curr_alipay = schema.load(params, unknown="exclude")
        ToolAlipayConfigService.update(curr_alipay=curr_alipay)
