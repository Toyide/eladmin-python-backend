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

# @Time    : 2022/6/13 19:36
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : job_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import Blueprint, request, session
from flask_restful import Api, Resource, marshal_with, inputs
from flask_restful.reqparse import RequestParser

from src.config import api_utils
from src.config.api_utils import build_params, oper_log, check_auth
from src.dto_mapper import job_page_fields, job_fields
from src.schema import JobSchema
from src.service.sys_service import JobService
from src.tools import format_date, download_excel

job_app = Blueprint('job', __name__, url_prefix='/api/job')
job_api = Api(job_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('name', location='json', type=str, trim=True, required=True)
parser.add_argument('jobSort', location='json', type=int, trim=True, required=True)
parser.add_argument('enabled', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=True)


@job_api.resource('', '/')
class JobAPI(Resource):
    @oper_log('查询岗位', request)
    @check_auth('job:list,user:list', request)
    @marshal_with(job_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return JobService.query_all(**params_dict)

    @oper_log('新增岗位', request)
    @check_auth('job:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = JobSchema()
        curr_job = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_job.create_by = user["username"]
        JobService.create(curr_job=curr_job)

    @oper_log('修改岗位', request)
    @check_auth('job:edit', request)
    def put(self):
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = JobSchema()
        curr_job = schema.load(params, unknown="exclude")
        user = session["user"]
        curr_job.update_by = user["username"]
        JobService.update(curr_job=curr_job)

    @oper_log('删除岗位', request)
    @check_auth('job:del', request)
    def delete(self):
        ids = request.get_json()
        JobService.delete(ids=ids)


@job_api.resource('/download')
class DownloadJobs(Resource):
    @oper_log('导出岗位数据', request)
    @check_auth('job:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = JobService.query_all(**params_dict)
        contents = []
        for job in pagination.items:
            data = OrderedDict()
            data["岗位名称"] = job.name
            data["岗位状态"] = "启用" if job.enabled else "停用"
            data["创建日期"] = format_date(job.create_time) if job.create_time else ""
            contents.append(data)

        return download_excel(contents)


@job_api.resource('/<int:_id>')
class GetJobById(Resource):
    @oper_log('根据ID查询岗位', request)
    @check_auth('job:list', request)
    @marshal_with(job_fields)
    def get(self, _id):
        data = JobService.find_by_id(job_id=_id)
        return data
