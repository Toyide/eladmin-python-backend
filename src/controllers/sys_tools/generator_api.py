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

# @Time    : 2022/8/9 11:25
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : generator_api.py
# @Project : eladmin_py_backend
import os
import tempfile
import zipfile

from flask import Blueprint, request, render_template, send_file
from flask_restful import Api, Resource, marshal, inputs
from flask_restful.reqparse import RequestParser

from src import ServerConfig
from src.config.api_utils import build_params, get_admin_path, create_file
from src.dto_mapper import column_fields
from src.extensions import AppException
from src.models import CodeGenConfig
from src.schema import CodeColumnConfigSchema
from src.service.sys_tools_service import GeneratorService, GenConfigService

generator_app = Blueprint('generator', __name__, url_prefix='/api/generator',
                          template_folder=os.path.abspath('templates'))
generator_api = Api(generator_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('tableName', location='json', type=str, trim=True, required=True)
parser.add_argument('columnName', location='json', type=str, trim=True, required=True)
parser.add_argument('columnType', location='json', type=str, trim=True, required=True)
parser.add_argument('dictName', location='json', type=str, trim=True, required=False)
parser.add_argument('extra', location='json', type=str, trim=True, required=False)
parser.add_argument('formType', location='json', type=str, trim=True, required=False)
parser.add_argument('keyType', location='json', type=str, trim=True, required=False)
parser.add_argument('queryType', location='json', type=str, trim=True, required=False)
parser.add_argument('remark', location='json', type=str, trim=True, required=False)
parser.add_argument('dateAnnotation', location='json', type=str, trim=True, required=False)
parser.add_argument('formShow', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('listShow', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('notNull', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)


def preview(columns: list, gen_config: CodeGenConfig):
    if not gen_config.config_id:
        raise AppException("请先配置生成器!")
    gen_list = []
    gen_dict = GeneratorService.get_gen_dict(columns, gen_config)
    templates = GeneratorService.get_templates()
    for t in templates:
        name = os.path.basename(t)
        render_result = {"content": render_template(name, **gen_dict), "name": name}
        gen_list.append(render_result)
    return gen_list


def generator(columns: list, gen_config: CodeGenConfig):
    if not gen_config.config_id:
        raise AppException("请先配置生成器!")
    gen_dict = GeneratorService.get_gen_dict(columns, gen_config)
    templates = GeneratorService.get_templates()
    root_path = os.path.join(tempfile.gettempdir(), "snowadmin-gen-temp", gen_config.table_name)
    for t in templates:
        name = os.path.basename(t)
        path = get_admin_path(name, gen_config.module_name, gen_config.pack, gen_dict["className"].lower(),
                              root_path=root_path)
        if not gen_config.cover and os.path.exists(path):
            continue
        content = render_template(name, **gen_dict)
        create_file(path, content)


def download(columns: list, gen_config: CodeGenConfig):
    if not gen_config.config_id:
        raise AppException("请先配置生成器!")
    gen_dict = GeneratorService.get_gen_dict(columns, gen_config)
    templates = GeneratorService.get_templates()
    root_path = os.path.join(tempfile.gettempdir(), "snowadmin-gen-temp", gen_config.table_name)
    zip_file_name = f'{gen_config.table_name}.zip'
    zip_file_path = os.path.join(root_path, zip_file_name)
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    print(f"创建zip文件：{zip_file_path}")
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_STORED) as zip_file:
        for t in templates:
            name = os.path.basename(t)
            path = get_admin_path(name, gen_config.module_name, gen_config.pack, gen_dict["className"].lower(),
                                  root_path=root_path)
            if not gen_config.cover and os.path.exists(path):
                continue
            content = render_template(name, **gen_dict)
            create_file(path, content)
            zip_file.write(path, path.replace(root_path, ""))
    return send_file(zip_file_path, mimetype='zip', attachment_filename=zip_file_name, as_attachment=True)


@generator_api.resource('/tables')
class GetTables(Resource):
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination_dict = GeneratorService.get_tables(**params_dict)
        return pagination_dict


@generator_api.resource('/columns')
class GetColumns(Resource):
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        table_name = params_dict["tableName"]
        columns = GeneratorService.get_columns(table_name=table_name)
        return {"totalElements": len(columns), "content": [marshal(d, column_fields) for d in columns]}


@generator_api.resource('/<table_name>/<int:opt_type>')
class Generator(Resource):
    def post(self, table_name, opt_type):
        if not ServerConfig.generator_enabled and opt_type == 0:
            raise AppException("此环境不允许生成代码，请选择预览或者下载查看！")
        conf = GenConfigService.find(table_name=table_name)
        columns = GeneratorService.get_columns(table_name=table_name)
        if opt_type == 0:  # 生成代码
            generator(columns, conf)
        elif opt_type == 1:  # 预览
            return preview(columns, conf)
        elif opt_type == 2:  # 打包
            return download(columns, conf)
        else:
            raise AppException("无效的参数！")


@generator_api.resource('', '/')
class GeneratorUpdate(Resource):
    def put(self):
        parser_put = parser.copy()
        nested_parser = RequestParser()
        nested_parser.parse_args(req=parser_put)
        params = request.get_json()
        schema = CodeColumnConfigSchema()
        curr_configs = schema.load(params, unknown="exclude", many=True)
        GeneratorService.save(curr_configs=curr_configs)


@generator_api.resource('/sync')
class GeneratorSync(Resource):

    def post(self):
        tables = request.json
        GeneratorService.sync(tables=tables)
