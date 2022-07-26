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

# @Time    : 2022/7/19 19:14
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : server_deploy_api.py
# @Project : eladmin_py_backend

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with
from flask_restful.reqparse import RequestParser

from src.config.api_utils import build_params, check_auth, datetime_parse, oper_log
from src.dto_mapper import server_deploy_page_fields, server_deploy_fields
from src.schema import MntServerSchema
from src.service.devops_service import ServerDeployService

server_deploy_app = Blueprint('server_deploy', __name__, url_prefix='/api/serverDeploy')
server_deploy_api = Api(server_deploy_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('account', location='json', type=str, trim=True, required=False)
parser.add_argument('ip', location='json', type=str, trim=True, required=False)
parser.add_argument('name', location='json', type=str, trim=True, required=False)
parser.add_argument('password', location='json', type=str, trim=True, required=False)
parser.add_argument('port', location='json', type=int, trim=True, required=False)


@server_deploy_api.resource('', '/')
class ServerDeployAPI(Resource):
    @oper_log('查询服务器', request)
    @check_auth('serverDeploy:list', request)
    @marshal_with(server_deploy_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = ServerDeployService.query_all(**params_dict)
        return pagination

    @oper_log('新增服务器', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = MntServerSchema()
        curr_data = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_data.create_by = user["username"]
        ServerDeployService.create(curr_data=curr_data)

    @oper_log('修改服务器', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = MntServerSchema()
        curr_data = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_data.update_by = user["username"]
        ServerDeployService.update(curr_data=curr_data)

    @oper_log('删除服务器', request)
    def delete(self):
        ids = request.get_json()
        ServerDeployService.delete(ids=ids)


@server_deploy_api.resource('/download')
class DownloadMntServers(Resource):
    @oper_log('导出服务器', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = ServerDeployService.query_all(**params_dict)
        return ServerDeployService.download(data_list=pagination.items)


@server_deploy_api.resource('/<int:_id>')
class GetServerById(Resource):
    @oper_log('根据ID查询服务器', request)
    @marshal_with(server_deploy_fields)
    def get(self, _id):
        data = ServerDeployService.find_by_id(server_id=_id)
        return data


@server_deploy_api.resource('/testConnect')
class TestConnectServerAPI(Resource):
    @oper_log('测试连接服务器', request)
    def post(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = MntServerSchema()
        curr_server = schema.load(params, unknown="exclude")
        return ServerDeployService.test_connect(curr_server=curr_server)
