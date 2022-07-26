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

# @Time    : 2022/5/24 14:30
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : api_utils.py
# @Project : eladmin_py_backend
import datetime
import functools
import hashlib
import json
import os
import re
import traceback
import warnings
from copy import copy

import psutil
import requests
from flask_restful import marshal

from src import ServerConfig, redis_client
from src.extensions import AppException

column_type_convert = {"tinyint": "BigInteger",
                       "smallint": "BigInteger",
                       "mediumint": "BigInteger",
                       "int": "BigInteger",
                       "integer": "BigInteger",
                       "bigint": "BigInteger",
                       "float": "Numeric",
                       "double": "Numeric",
                       "decimal": "Numeric",
                       "bit": "bit",
                       "char": "String",
                       "varchar": "String",
                       "tinytext": "String",
                       "text": "String",
                       "mediumtext": "String",
                       "longtext": "String",
                       "date": "DateTime",
                       "datetime": "DateTime",
                       "timestamp": "DateTime"}

datetime_parse = lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")


def build_menu_tree(menu_tree):
    def build_component(curr):
        if not curr['iframe']:
            if curr['pid'] is None:
                return 'Layout' if curr['component'] is None or len(curr['component']) == 0 else curr['component']
            elif curr['component'] and len(curr['component']) > 0:
                return curr['component']

    def build_meta(curr):
        return {'title': curr['title'], 'icon': curr['icon'], 'cache': not curr['cache']}

    rs = []
    for m in menu_tree:
        if m:
            mvo = {
                "name": m['name'] if m['name'] else m['title'],
                "path": '/' + m['path'] if m['pid'] is None else m['path'],  # 一级目录需要加斜杠，不然会报警告
                "hidden": m['hidden'],
                "component": build_component(m),
                "meta": build_meta(m),
            }
            if m.get('children') and len(m.get('children')) != 0:
                mvo["alwaysShow"] = True
                mvo["redirect"] = "noredirect"
                mvo["children"] = build_menu_tree(m['children'])
            elif m['pid'] is None:
                mvo1 = {
                    "meta": mvo["meta"],
                }
                if not m['iframe']:
                    mvo1["path"] = "index"
                    mvo1["name"] = m['name']
                    mvo1["component"] = m['component']
                else:
                    mvo1["path"] = m['path']
                mvo["name"] = None
                mvo["meta"] = None
                mvo["component"] = "Layout"
                mvo["children"] = [mvo1]

            rs.append(mvo)
    return rs


def build_params(params: list) -> dict:
    params_dict = {}
    for k, v in params:
        if k not in params_dict:
            params_dict[k] = v
        else:
            # createTime是2个，sort也可能是多个
            p_list = [params_dict[k], v]
            params_dict[k] = p_list
    if 'sort' in params_dict and type(params_dict['sort']) == str:  # sort统一按list处理
        params_dict['sort'] = [params_dict['sort']]
    return params_dict


GB = 1024 * 1024 * 1024
MB = 1024 * 1024
KB = 1024


def get_size(size: int):
    if size / GB >= 1:
        rs = f"{round(size / GB, 2)}GB   "
    elif size / MB >= 1:
        rs = f"{round(size / MB, 2)}MB   "
    elif size / KB >= 1:
        rs = f"{round(size / KB, 2)}KB   "
    else:
        rs = f"{size}B   "
    return rs


def get_file_type(suffix: str) -> str:
    documents = "txt doc pdf ppt pps xlsx xls docx"
    music = "mp3 wav wma mpa ram ra aac aif m4a"
    video = "avi mpg mpe mpeg asf wmv mov qt rm mp4 flv m4v webm ogv ogg"
    image = "bmp dib pcp dif wmf gif jpg tif eps psd cdr iff tga pcd mpt png jpeg"
    if suffix.lower() in image:
        return "图片"
    elif suffix.lower() in documents:
        return "文档"
    elif suffix.lower() in music:
        return "音乐"
    elif suffix.lower() in video:
        return "视频"
    else:
        return "其他"


def test_connect(curr_db) -> bool:
    sobj = None
    try:
        from sqlalchemy import or_, create_engine
        from sqlalchemy.orm import sessionmaker
        arr = curr_db.jdbc_url.split("//")
        some_engine = create_engine(f'{arr[0]}//{curr_db.user_name}:{curr_db.pwd}@{arr[1]}')
        SessionClass = sessionmaker(bind=some_engine)
        sobj = SessionClass()
    except Exception as e:
        print(e)
        return False
    finally:
        if sobj:
            sobj.close()
    return True


def read_sql_list(sql_file: str) -> list:
    with open(sql_file, 'r+', encoding='utf-8', errors="ignore") as f:
        lines = f.readlines()
    sql_list = []
    sub_list = []
    for line in lines:
        temp = line.strip()
        if temp.endswith(";"):
            sub_list.append(temp)
            sql_list.append("".join(sub_list))
            sub_list.clear()
        else:
            sub_list.append(temp)
    if sub_list:
        sql_list.append("".join(sub_list))
    return sql_list


def batch_execute(conn, sql_list: list):
    for sql in sql_list:
        conn.execute(sql)


def execute_file(curr_db, execute_file) -> str:
    sobj = None
    try:
        from sqlalchemy import or_, create_engine
        from sqlalchemy.orm import sessionmaker
        arr = curr_db.jdbc_url.split("//")
        some_engine = create_engine(f'{arr[0]}//{curr_db.user_name}:{curr_db.pwd}@{arr[1]}')
        SessionClass = sessionmaker(bind=some_engine)
        sobj = SessionClass()
        batch_execute(sobj, read_sql_list(execute_file))
    except Exception as e:
        raise e
    finally:
        if sobj:
            sobj.close()
    return "success"


def toCamelCase(s: str) -> str:
    if s:
        s = s.lower()
    rs = ""
    upper_case = False
    for x in s:
        if x == '_':
            upper_case = True
        elif upper_case:
            rs += x.upper()
            upper_case = False
        else:
            rs += x
    return rs


def toCapitalizeCamelCase(s: str) -> str:
    if not s:
        return s
    s = toCamelCase(s)
    return s[0].upper() + s[1:]


def get_addr(remote_addr):
    address = ""
    try:
        rs = requests.get(ServerConfig.ip_url % remote_addr)
        address = rs.json()["addr"] if rs and rs.json() else ""
    except:
        pass
    return address


def upload_sm_ms(params):
    """
    上传文件到sm.ms
    :param params: 文件
    :return:
    """
    headers = {"Authorization": ServerConfig.sm_ms_token}
    rsp = requests.post(f"{ServerConfig.sm_ms_url}/v2/upload", files=params, headers=headers, timeout=10)
    # {'success': True, 'code': 'success', 'message': 'Get list success.', 'data': [{'file_id': 0, 'width': 2592, 'height': 1936, 'filename': 'IMG_1357.JPG', 'storename': 'z7O5mheKI16BTZg.jpg', 'size': 3172026, 'path': '/2020/08/22/z7O5mheKI16BTZg.jpg', 'hash': 'bESqgwDI5eszJfv41t7TpFxdAG', 'url': 'https://i.loli.net/2020/08/22/z7O5mheKI16BTZg.jpg', 'delete': 'https://sm.ms/delete/bESqgwDI5eszJfv41t7TpFxdAG', 'page': 'https://sm.ms/image/z7O5mheKI16BTZg'}], 'RequestId': '843522DB-A2AF-45E7-BE4A-89E5FA58FC1C'}
    # {'success': True, 'code': 'success', 'message': 'Upload success.', 'data': {'file_id': 0, 'width': 200, 'height': 200, 'filename': '25ba0efa-e458-11ea-941a-f0def17fd672_avatar_test.png', 'storename': 'NPF3hucopq9z4WZ.png', 'size': 83824, 'path': '/2020/08/22/NPF3hucopq9z4WZ.png', 'hash': 'EFVHL9YjhpufCv4ybqsGKBiORd', 'url': 'https://i.loli.net/2020/08/22/NPF3hucopq9z4WZ.png', 'delete': 'https://sm.ms/delete/EFVHL9YjhpufCv4ybqsGKBiORd', 'page': 'https://sm.ms/image/NPF3hucopq9z4WZ'}, 'RequestId': 'B2E568A8-96D3-408A-96E8-03ADA288A9F0'}
    rs = rsp.json()
    code, data, msg = rs.get("code"), rs.get("data"), rs.get("message")
    if code != "success":
        raise AppException(msg)
    return data[0] if isinstance(data, list) else data


def get_ip():
    info = psutil.net_if_addrs()
    for k, v in info.items():
        for item in v:
            if item[0] == 2 and not item[1] == '127.0.0.1':
                return item[1]
    return None


def oper_log(desc: str, req):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.simplefilter('ignore', RuntimeWarning)
            token = req.headers.environ.get('HTTP_AUTHORIZATION')
            key = f"{ServerConfig.online_key}{token[7:]}"
            user = json.loads(redis_client.get(key))
            username = user.get("username")
            from src.models import Logs
            log_model = Logs()
            log_model.description = desc
            log_model.log_type = "INFO"
            log_model.method = f'{func.__module__}.{func.__name__}'
            params = {"path": req.path}
            if req.json:
                params["json"] = copy(req.json)
            if req.form:
                params["form"] = copy(req.form)
            if req.args:
                req_args = req.args.items(multi=True)
                params["args"] = build_params(req_args)
            log_model.params = json.dumps(params, ensure_ascii=False)
            log_model.request_ip = get_ip()
            log_model.log_time = 0
            log_model.username = username
            # log_model.address = get_addr(req.remote_addrs)
            log_model.browser = f'{req.user_agent.browser}({req.user_agent.version})/{req.user_agent.platform}'
            start = datetime.datetime.now()
            try:
                rs = func(*args, **kwargs)
            except Exception as e:
                log_model.log_type = 'ERROR'
                log_model.exception_detail = traceback.format_exc()
                raise e
            finally:
                log_model.log_time = (datetime.datetime.now() - start).microseconds / 1000
                from src.service.sys_service import LogService
                LogService.save(log_model)
            return rs

        return wrapper

    return decorator


def get_keys(kw, key_param):
    # id:#user.id -> id #user.id
    if len(kw) == 0:
        raise AppException("必须使用Key:Value传参")
    keys = {}
    param_str = re.sub(r"[^\w.#]", " ", key_param)
    for x in param_str.split():
        for k, v in kw.items():
            params = x[1:].split(".")
            if x.startswith("#") and k == params[0]:
                if len(params) == 3:  # 最多支持3层，如user.role.id
                    if isinstance(v, dict):
                        keys[x] = v[params[1]][params[2]]
                    elif isinstance(v, object):
                        v1 = getattr(v, params[1])
                        keys[x] = getattr(v1, params[2])
                elif len(params) == 2:
                    if isinstance(v, dict):
                        keys[x] = v[params[1]]
                    elif isinstance(v, object):
                        keys[x] = getattr(v, params[1])
                elif len(params) == 1:
                    keys[x] = v
    rep = dict((re.escape(k), v) for k, v in keys.items())
    pt = re.compile("|".join(rep.keys()))
    key = pt.sub(lambda m: str(rep[re.escape(m.group(0))]), key_param)
    return key


def cacheable(key, schema_class, data_fields, many=False):
    """
    存在缓存则返回，否则设置缓存为函数返回值
    :param key: redis key
    :param schema_class: Marshmallow Schema
    :param data_fields: Flask-Restful Fields
    :param many: Schema参数
    :return:
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if redis_client.exists(key):
                val = redis_client.get(key)
                cache_dict = json.loads(val)
                schema = schema_class()
                rs = schema.load(cache_dict, unknown="exclude", many=many)
            else:
                rs = func(*args, **kwargs)
                cache_dict = marshal(rs, data_fields)
                redis_client.set(key, json.dumps(cache_dict, ensure_ascii=False))
            return rs

        return wrapper

    return decorator


def check_auth(role: str, req):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            token = req.headers.environ.get('HTTP_AUTHORIZATION')
            key = f"{ServerConfig.online_key}{token[7:]}"
            user = json.loads(redis_client.get(key))
            roles = user.get("roles")  # 用户权限
            role_arr = role.split(",")  # 待检查权限
            # 待检查权限中只要有任何一个在用户权限中即可操作
            if roles is None or ('admin' not in roles and all(r.strip() not in roles for r in role_arr)):
                raise AppException("您没有权限操作，请联系管理员！")
            rs = func(*args, **kwargs)
            return rs

        return wrapper

    return decorator


def get_admin_path(template_name: str, module_name: str, pack: str, class_name: str, root_path=os.path.expanduser('~')):
    package_path = os.path.join(root_path, module_name)
    # package_path = os.path.join(project_path, "eladmin_py_backend", "src")
    # if pack:
    #     package_path = os.path.join(package_path, pack)
    if "Api.html" == template_name:
        return os.path.normpath(os.path.join(package_path, "controllers", class_name + "_api.py"))
    if "Entity.html" == template_name:
        return os.path.normpath(os.path.join(package_path, class_name + "_model.py"))
    elif "Mapper.html" == template_name:
        return os.path.normpath(os.path.join(package_path, class_name + "_mapper.py"))
    elif "Schema.html" == template_name:
        return os.path.normpath(os.path.join(package_path, class_name + "_schema.py"))
    elif "Service.html" == template_name:
        return os.path.normpath(os.path.join(package_path, "service", class_name + "_service.py"))


def create_file(path: str, content: str):
    try:
        full_path = os.path.normpath(path)
        print(f"创建文件：{full_path}")
        dir_path = os.path.dirname(full_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(path, "w+", encoding="utf-8", errors="ignore") as f:
            f.write(content)
    except:
        traceback.print_exc()


def get_md5(file_path: str) -> str:
    if not os.path.isfile(file_path):
        return ""
    else:
        length = 1024
        m = hashlib.md5()
        with open(file_path, 'rb') as f:
            while True:
                b = f.read(length)
                if not b:
                    break
                m.update(b)
    return m.hexdigest().upper()


def batch_clear(name: str):
    for key in redis_client.scan_iter(name):
        redis_client.delete(key)


def build_sorts(sorts: list, fields: dict, clazz: object) -> list:
    """
    构造排序条件
    :param sorts: 前端传参，如sort=level%2Casc
    :param fields: DTO <--> DB Model转换定义
    :param clazz: DB Model类
    :return: list
    """
    sort_params = []
    if sorts:
        sort_items = [sort.split(',') for sort in sorts]
        if sort_items:
            for sort_item, sort_direction in sort_items:
                if sort_item in fields:
                    field_obj = fields[sort_item]
                    attr = field_obj.attribute if hasattr(field_obj, "attribute") else sort_item
                    if hasattr(clazz, attr):
                        field_attr = getattr(clazz, attr)
                        sort_params.append(field_attr.desc() if sort_direction == 'desc' else field_attr.asc())
    return sort_params
