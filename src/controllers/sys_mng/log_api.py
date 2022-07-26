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

# @Time    : 2022/7/12 18:19
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : log_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with

from src.config import api_utils
from src.config.api_utils import check_auth
from src.dto_mapper import logs_page_fields, logs_fields
from src.service.sys_service import LogService
from src.tools import download_excel, format_date

log_app = Blueprint('log', __name__, url_prefix='/api/logs')
log_api = Api(log_app)


@log_api.resource('', '/')
class LogsApi(Resource):
    @check_auth('', request)
    @marshal_with(logs_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        params_dict["logType"] = 'INFO'
        return LogService.query_all(**params_dict)


@log_api.resource('/user')
class GetUserLogs(Resource):
    @marshal_with(logs_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        data = session["user"]
        params_dict["blurry"] = data["username"]
        params_dict["logType"] = 'INFO'
        return LogService.query_all(**params_dict)


@log_api.resource('/error/<int:_id>')
class GetErrorLogById(Resource):
    @check_auth('', request)
    @marshal_with(logs_fields)
    def get(self, _id):
        return LogService.find_by_err_detail(_id=_id)


@log_api.resource('/error')
class GetErrorLogs(Resource):
    @check_auth('', request)
    @marshal_with(logs_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        params_dict["logType"] = 'ERROR'
        return LogService.query_all(**params_dict)


@log_api.resource('/del/error')
class DelAllByError(Resource):
    @check_auth('', request)
    def delete(self):
        return LogService.del_all_by_error()


@log_api.resource('/del/info')
class DelAllByInfo(Resource):
    @check_auth('', request)
    def delete(self):
        return LogService.del_all_by_info()


@log_api.resource('/download')
class DownloadLogs(Resource):
    @check_auth('', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        params_dict["logType"] = 'INFO'
        pagination = LogService.query_all(**params_dict)
        contents = []
        for _log in pagination.items:
            data = OrderedDict()
            data["用户名"] = _log.username
            data["IP"] = _log.request_ip
            data["IP来源"] = _log.address
            data["描述"] = _log.description
            data["浏览器"] = _log.browser
            data["请求耗时/毫秒"] = _log.log_time
            data["异常详情"] = _log.exception_detail if _log.exception_detail else ""
            data["创建日期"] = format_date(_log.create_time) if _log.create_time else ""
            contents.append(data)

        return download_excel(contents)


@log_api.resource('/error/download')
class DownloadErrLogs(Resource):
    @check_auth('', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        params_dict["logType"] = 'ERROR'
        pagination = LogService.query_all(**params_dict)
        contents = []
        for _log in pagination.items:
            data = OrderedDict()
            data["用户名"] = _log.username
            data["IP"] = _log.request_ip
            data["IP来源"] = _log.address
            data["描述"] = _log.description
            data["浏览器"] = _log.browser
            data["请求耗时/毫秒"] = _log.log_time
            data["异常详情"] = _log.exception_detail if _log.exception_detail else ""
            data["创建日期"] = format_date(_log.create_time) if _log.create_time else ""
            contents.append(data)

        return download_excel(contents)
