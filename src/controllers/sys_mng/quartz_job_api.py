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

# @Time    : 2022/7/6 20:23
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : quartz_jobs_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with, inputs
from flask_restful.reqparse import RequestParser

from src.config.api_utils import build_params, check_auth
from src.dto_mapper import quartz_job_page_fields, quartz_log_page_fields, quartz_job_fields
from src.schema import QuartzJobSchema
from src.service.quartz_service import QuartzJobService
from src.tools import format_date, download_excel

quartz_job_app = Blueprint('quartz_job', __name__, url_prefix='/api/jobs')
quartz_job_api = Api(quartz_job_app)


def email_type(value):
    if value is None or value == '':
        return value
    return inputs.regex(
        r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')(
        value)


parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('jobName', location='json', type=str, trim=True, required=True)
parser.add_argument('beanName', location='json', type=str, trim=True, required=True)
parser.add_argument('methodName', location='json', type=str, trim=True, required=True)
parser.add_argument('cronExpression', location='json', type=str, trim=True, required=True)
parser.add_argument('params', location='json', type=str, trim=True, required=False)
parser.add_argument('subTask', location='json', type=str, trim=True, required=False)
parser.add_argument('pauseAfterFailure', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('isPause', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('personInCharge', location='json', type=str, trim=True, required=True)
parser.add_argument('email', location='json', type=email_type,
                    trim=True, required=False, help='格式错误: {error_msg}')
parser.add_argument('description', location='json', type=str, trim=True, required=True)


@quartz_job_api.resource('', '/')
class QuartzJobAPI(Resource):
    @check_auth('timing:list', request)
    @marshal_with(quartz_job_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = QuartzJobService.query_all(**params_dict)
        return pagination

    @check_auth('timing:add', request)
    def post(self):
        parser_update = parser.copy()
        parser.remove_argument('id')
        parser_update.parse_args()
        user = session["user"]
        schema = QuartzJobSchema()
        curr_quartz_job = schema.load(request.get_json(), unknown="exclude")
        curr_quartz_job.create_by = user["username"]
        QuartzJobService.create(curr_quartz_job=curr_quartz_job)

    @check_auth('timing:del', request)
    def delete(self):
        ids = request.get_json()
        QuartzJobService.delete(ids=ids)

    @check_auth('timing:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        user = session["user"]
        schema = QuartzJobSchema()
        curr_quartz_job = schema.load(request.get_json(), unknown="exclude")
        curr_quartz_job.update_by = user["username"]
        QuartzJobService.update(curr_quartz_job=curr_quartz_job)
        return None, 204


@quartz_job_api.resource('/exec/<int:job_id>')
class ExecQuartzJob(Resource):
    @check_auth('timing:edit', request)
    def put(self, job_id: int):
        QuartzJobService.execution(QuartzJobService.find_by_id(job_id=job_id))
        return None, 204


@quartz_job_api.resource('/<int:job_id>')
class UpdateIsPause(Resource):
    @check_auth('timing:edit', request)
    def put(self, job_id: int):
        QuartzJobService.update_job(QuartzJobService.find_by_id(job_id=job_id))
        return None, 204


@quartz_job_api.resource('/logs')
class QuartzLogAPI(Resource):
    @check_auth('timing:list', request)
    @marshal_with(quartz_log_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = QuartzJobService.query_all_log(**params_dict)
        return pagination


@quartz_job_api.resource('/download')
class DownloadQuartzJobs(Resource):
    @check_auth('timing:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = QuartzJobService.query_all(**params_dict)
        contents = []
        for q_job in pagination.items:
            data = OrderedDict()
            data["任务名称"] = q_job.job_name
            data["Bean名称"] = q_job.bean_name
            data["执行方法"] = q_job.method_name
            data["参数"] = q_job.description
            data["表达式"] = q_job.cron_expression
            data["状态"] = "暂停中" if q_job.is_pause else "运行中"
            data["描述"] = q_job.description
            data["创建日期"] = format_date(q_job.create_time) if q_job.create_time else ""
            contents.append(data)

        return download_excel(contents)


@quartz_job_api.resource('/logs/download')
class DownloadQuartzLogs(Resource):
    @check_auth('timing:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = QuartzJobService.query_all_log(**params_dict)
        contents = []
        for q_log in pagination.items:
            data = OrderedDict()
            data["任务名称"] = q_log.job_name
            data["Bean名称"] = q_log.bean_name
            data["执行方法"] = q_log.method_name
            data["参数"] = q_log.params
            data["表达式"] = q_log.cron_expression
            data["异常详情"] = q_log.exception_detail
            data["耗时/毫秒"] = q_log.log_time
            data["状态"] = "成功" if q_log.is_success else "失败"
            data["创建日期"] = format_date(q_log.create_time) if q_log.create_time else ""
            contents.append(data)

        return download_excel(contents)


@quartz_job_api.resource('/<int:_id>')
class GetQuartzJobById(Resource):
    @check_auth('timing:list', request)
    @marshal_with(quartz_job_fields)
    def get(self, _id):
        data = QuartzJobService.find_by_id(job_id=_id)
        return data
