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

# @Time    : 2022/8/15 15:01
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : genConfig_api.py
# @Project : eladmin_py_backend
from flask import Blueprint, request
from flask_restful import Api, Resource, inputs, marshal_with
from flask_restful.reqparse import RequestParser

from src.dto_mapper import gen_config_fields
from src.schema import GenConfigSchema
from src.service.sys_tools_service import GenConfigService

genConfig_app = Blueprint('genConfig', __name__, url_prefix='/api/genConfig')
genConfig_api = Api(genConfig_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=False)
parser.add_argument('tableName', location='json', type=str, trim=True, required=True)
parser.add_argument('author', location='json', type=str, trim=True, required=True)
parser.add_argument('pack', location='json', type=str, trim=True, required=True)
parser.add_argument('path', location='json', type=str, trim=True, required=True)
parser.add_argument('moduleName', location='json', type=str, trim=True, required=True)
parser.add_argument('apiPath', location='json', type=str, trim=True, required=False)
parser.add_argument('prefix', location='json', type=str, trim=True, required=False)
parser.add_argument('apiAlias', location='json', type=str, trim=True, required=True)
parser.add_argument('cover', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=True)


@genConfig_api.resource('', '/')
class GenConfigAPI(Resource):
    @marshal_with(gen_config_fields)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = GenConfigSchema()
        curr_gen = schema.load(params, unknown="exclude")
        return GenConfigService.update(curr_gen=curr_gen)


@genConfig_api.resource('/<table_name>')
class GetGenConfig(Resource):
    @marshal_with(gen_config_fields)
    def get(self, table_name):
        return GenConfigService.find(table_name=table_name)
