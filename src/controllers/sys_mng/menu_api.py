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

# @Time    : 2022/5/23 23:27
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : menu_api.py
# @Project : eladmin_py_backend
from collections import OrderedDict

from flask import Blueprint, request, session
from flask_restful import Resource, Api, marshal_with, marshal, inputs
from flask_restful.reqparse import RequestParser

from src.config import api_utils
from src.config.api_utils import build_params, oper_log, check_auth
from src.dto_mapper import menu_page_fields, menu_fields
from src.schema import MenuSchema
from src.service.sys_service import MenuService
from src.tools import format_date, download_excel

menu_app = Blueprint('menu', __name__, url_prefix='/api/menus')
menu_api = Api(menu_app)

parser = RequestParser()
parser.add_argument('id', location='json', type=int, trim=True, required=True)
parser.add_argument('pid', location='json', type=int, trim=True, required=False)
parser.add_argument('title', location='json', type=str, trim=True, required=True)
parser.add_argument('path', location='json', type=str, trim=True, required=True)
parser.add_argument('menuSort', location='json', type=int, trim=True, required=True)
parser.add_argument('component', location='json', type=str, trim=True)
parser.add_argument('componentName', location='json', type=str, trim=True)
parser.add_argument('icon', location='json', type=str, trim=True)
parser.add_argument('iframe', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False,'1','0',1,0,None),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('cache', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('hidden', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('type', location='json', type=int, trim=True, required=False)
parser.add_argument('permission', location='json', type=str, trim=True, required=False)
parser.add_argument('subCount', location='json', type=int, trim=True, required=False)
parser.add_argument('hasChildren', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('leaf', location='json', type=inputs.boolean,
                    choices=('true', 'false', 'True', 'False', True, False),
                    help='无效的选项: {error_msg}', trim=True, required=False)
parser.add_argument('label', location='json', type=str, trim=True, required=False)


@menu_api.resource('', '/')
class MenuApi(Resource):
    @oper_log('查询菜单', request)
    @check_auth('menu:list', request)
    @marshal_with(menu_page_fields)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = api_utils.build_params(params)
        return MenuService.query_all(**params_dict)

    @oper_log('新增菜单', request)
    @check_auth('menu:add', request)
    def post(self):
        parser_post = parser.copy()
        parser_post.remove_argument('id')
        parser_post.parse_args()
        params = request.get_json()
        schema = MenuSchema()
        curr_menu = schema.load(params, unknown="exclude")
        data = session["user"]
        curr_menu.sub_count = 0
        curr_menu.create_by = data["username"]
        MenuService.create(curr_menu=curr_menu)

    @oper_log('修改菜单', request)
    @check_auth('menu:edit', request)
    def put(self):
     
        parser_put = parser.copy()
        parser_put.parse_args()
        params = request.get_json()
        schema = MenuSchema()
        curr_menu = schema.load(params, unknown="exclude")
        data = session["user"]
        curr_menu.update_by = data["username"]
        MenuService.update(curr_menu=curr_menu)
        return None, 204

    @oper_log('删除菜单', request)
    @check_auth('menu:del', request)
    def delete(self):
        ids = request.get_json()
        menu_set = set()
        for _id in ids:
            menus = MenuService.get_menus(pid=_id)
            menu_set.add(MenuService.find_by_id(menu_id=_id))
            MenuService.get_delete_menus(menu_list=menus, menu_set=menu_set)

        MenuService.delete(menu_set=menu_set)


@menu_api.resource('/build')
class BuildMenus(Resource):
    @oper_log('获取前端所需菜单', request)
    def get(self):
        user = session["user"]
        menus = MenuService.find_by_user(user_id=user['id'])
        schema = MenuSchema()
        tree = MenuService.get_menu_tree(list(filter(lambda x: x['type'] != 2, [schema.dump(m) for m in menus])))
        return tree


@menu_api.resource('/lazy')
class LazyGetMenus(Resource):
    @oper_log('返回全部的菜单', request)
    @check_auth('menu:list,roles:list', request)
    def get(self):
        pid = request.args.get("pid", type=int)
        menus = MenuService.get_menus(pid=pid)
        rs = [marshal(m, menu_fields) for m in menus]
        return rs


@menu_api.resource('/superior')
class GetSuperior(Resource):
    @oper_log('查询菜单', request)
    @check_auth('menu:list', request)
    def post(self):
        ids = request.get_json()
        if ids:
            menus_superior = set()
            all_menus = MenuService.query_all_menus()
            menu_list = []
            parent_dict = {}
            menu_dict = {}
            for m in all_menus:
                menu_dict[m.menu_id] = m
                if m.menu_id in ids:
                    menu_list.append(m)
                children = parent_dict.get(m.pid)
                if children is None:
                    children = []
                    parent_dict[m.pid] = children
                children.append(m)
            for menu in menu_list:
                superiors = MenuService.get_superior(menu=menu, menus=[], parent_dict=parent_dict, menu_dict=menu_dict)
                superior_temp = list(set(superiors))
                superior_temp.sort(key=superiors.index)
                menus_superior.update(set(superior_temp))
            menus = MenuService.build_tree(list(menus_superior))
        else:
            menus = MenuService.get_menus()
        return [marshal(m, menu_fields) for m in menus]


@menu_api.resource('/download')
class DownloadMenus(Resource):
    @oper_log('导出菜单数据', request)
    @check_auth('menu:list', request)
    def get(self):
        params = request.args.items(multi=True)
        params_dict = build_params(params)
        pagination = MenuService.query_all(**params_dict)
        contents = []
        for menu in pagination.items:
            data = OrderedDict()
            data["菜单标题"] = menu.title
            data["菜单类型"] = "目录" if menu.type is None else "菜单" if menu.type == 1 else "按钮"
            data["权限标识"] = menu.permission
            data["外链菜单"] = "是" if menu.i_frame else "否"
            data["菜单可见"] = "否" if menu.hidden else "是"
            data["是否缓存"] = "否" if menu.cache else "是"
            data["创建日期"] = format_date(menu.create_time) if menu.create_time else ""
            contents.append(data)

        return download_excel(contents)


@menu_api.resource('/<int:_id>')
class GetMenuById(Resource):
    @oper_log('根据ID查菜单', request)
    @check_auth('menu:list', request)
    @marshal_with(menu_fields)
    def get(self, _id):
        data = MenuService.find_by_id(menu_id=_id)
        return data


@menu_api.resource('/child')
class GetChild(Resource):
    @oper_log('权限关联界面勾选子菜单', request)
    @check_auth('menu:list', request)
    def get(self):
        id = request.args.get("id", type=int)
        child=[]
        #添加自身
        child.append(id)
        #添加孩子们
        for c in child:
            menus = MenuService.get_menus(c)
            for m in menus:
                child.append(m.menu_id)
        return child