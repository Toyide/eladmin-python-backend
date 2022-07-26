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

# @Time    : 2022/8/16 15:40
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : verify_api.py
# @Project : eladmin_py_backend
import datetime
import os

from flask import Blueprint, render_template, request
from flask_restful import Api, Resource

from src import ServerConfig
from src.config.api_utils import oper_log
from src.service.sys_service import VerifyService
from src.service.sys_tools_service import ToolEmailConfigService

verify_app = Blueprint('verify', __name__, url_prefix='/api/code', template_folder=os.path.abspath('templates'))
verify_api = Api(verify_app)


@verify_api.resource('/validated')
class VerifyAPI(Resource):
    def get(self):
        pass


@verify_api.resource('/resetEmail')
class ResetEmailAPI(Resource):
    @oper_log('修改邮箱', request)
    def post(self):
        email = request.args["email"]
        code, email_info = VerifyService.send_email(email=email, prefix=ServerConfig.email_reset_email_prefix)
        email_map = {"year": datetime.datetime.now().year, "code": code}
        email_info["content"] = render_template("Email.html", **email_map)
        ToolEmailConfigService.send(email_info)


@verify_api.resource('/email/resetPass')
class ResetPassAPI(Resource):
    def post(self):
        pass
