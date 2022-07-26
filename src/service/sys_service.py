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

# @Time    : 2022/5/31 20:54
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : user_service.py
# @Project : eladmin_py_backend
import datetime
import json
import os

from flask_restful import marshal
from sqlalchemy import or_, func

from src.config import api_utils, ServerConfig
from src.dto_mapper import dept_fields, menu_fields, dict_detail_fields, user_edit_fields, \
    role_edit_fields, job_fields, dict_fields, role_fields, logs_fields
from src.extensions import AppException
from src.models import User, Role, db, Dept, DictDetail, Dict, Job, \
    Menu, UsersRoles, Logs, redis_client
from src.schema import UserSchema, DeptSchema, MenuSchema, RoleSchema, DictSchema, JobSchema
from src.tools import random_code


class UserService:
    @staticmethod
    def query_all(page=0, size=10, **kwargs):
        # has_next: 是否还有下一页
        # has_prev: 是否还有上一页
        # items: 返回当前页的所有内容
        # next(error_out=False): 返回下一页的Pagination对象
        # prev(error_out=False): 返回上一页的Pagination对象
        # page: 当前页的页码(从1开始)
        # pages: 总页数
        # per_page: 每页显示的数量
        # prev_num: 上一页页码数
        # next_num: 下一页页码数
        # query: 返回创建这个Pagination对象的查询对象
        # total: 查询返回的记录总数
        # db.session.paginate(page, per_page=10, error_out=False)
        _id = kwargs.get('id')
        blurry = kwargs.get('blurry')
        enabled = kwargs.get('enabled')
        dept_ids = kwargs.get('deptId')
        create_times = kwargs.get('createTime')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, user_edit_fields, User)
        query = []
        if _id:
            query.append((User.user_id == _id))
        if enabled:
            query.append((User.enabled.is_(True if enabled == 'true' else False)))
        if dept_ids:
            query.append((User.dept_id.in_(dept_ids)))
        if blurry:
            query.append(or_(User.email.like(f'%{blurry}%'), User.username.like(f'%{blurry}%'),
                             User.nick_name.like(f'%{blurry}%')))
        if create_times and len(create_times) >= 2:
            query.append((User.create_time.between(create_times[0], create_times[1])))
        return User.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                         error_out=False)

    @staticmethod
    # @cacheable(f'user:username:#username')
    def find_by_name(user_name: str) -> User:
        key = f"user:username:{user_name}"
        user_str = redis_client.get(key)
        if user_str:
            user_dict = json.loads(user_str)
            schema = UserSchema()
            user = schema.load(user_dict, unknown="exclude")
        else:
            user = User.query.filter(User.username == user_name).one_or_none()
            user_dict = marshal(user, user_edit_fields)
            redis_client.set(key, json.dumps(user_dict, ensure_ascii=False))
        return user

    @staticmethod
    # @cacheable('id:#user_id')
    def find_by_id(user_id: int) -> User:
        key = f"user:id:{user_id}"
        user_str = redis_client.get(key)
        if user_str:
            user_dict = json.loads(user_str)
            schema = UserSchema()
            user = schema.load(user_dict, unknown="exclude")
        else:
            user = User.query.filter(User.user_id == user_id).one_or_none()
            if user is None:
                raise AppException(f'您所操作的对象已不存在!')
            user_dict = marshal(user, user_edit_fields)
            redis_client.set(key, json.dumps(user_dict, ensure_ascii=False))
        return user

    @staticmethod
    def check_level(curr_user_id: int, roles: list):
        curr_roles = Role.query.join(UsersRoles).join(User).filter(User.user_id == curr_user_id).all()
        min_level = min([x.level for x in curr_roles])
        # roles = Role.query.join(UsersRoles).join(User).filter(User.user_id == user_id).all()
        update_roles = Role.query.filter(Role.role_id.in_([x.role_id for x in roles])).all()
        update_min_level = min([x.level for x in update_roles])
        if min_level > update_min_level:
            raise AppException('您的角色权限不足!')

    @staticmethod
    def update(curr_user: User):
        user = User.query.filter(User.user_id == curr_user.user_id).one()
        if user is None or not user.user_id:
            raise AppException(f'修改的数据可能已不存在!')
        exist_username = User.query.filter(User.username == curr_user.username).one_or_none()
        if exist_username and exist_username.user_id != curr_user.user_id:
            raise AppException(f'{curr_user.username}已存在！')
        exist_email = User.query.filter(User.email == curr_user.email).one_or_none()
        if exist_email and exist_email.user_id != curr_user.user_id:
            raise AppException(f'{curr_user.email}已存在！')
        old_roles = [r.role_id for r in user.roles]
        new_roles = [r.role_id for r in curr_user.roles]
        if old_roles.sort() != new_roles.sort():
            redis_client.delete(f"data:user:{user.user_id}")
            redis_client.delete(f"menu:user:{user.user_id}")
            redis_client.delete(f"role:auth:{user.user_id}")
        user.username = curr_user.username
        user.email = curr_user.email
        user.enabled = curr_user.enabled
        user.dept_id = curr_user.dept.dept_id
        user.phone = curr_user.phone
        user.nick_name = curr_user.nick_name
        user.gender = curr_user.gender
        user.update_by = curr_user.update_by
        user.update_time = datetime.datetime.now()
        user.dept = Dept.query.filter(Dept.dept_id == curr_user.dept.dept_id).one()
        user.roles = Role.query.filter(Role.role_id.in_(new_roles)).all()
        user.jobs = Job.query.filter(Job.job_id.in_([j.job_id for j in curr_user.jobs])).all()
        db.session.commit()
        redis_client.delete(f"user:id:{user.user_id}")
        redis_client.delete(f"user:username:{user.username}")
        user_dict = marshal(user, user_edit_fields)
        user_str = json.dumps(user_dict, ensure_ascii=False)
        redis_client.set(f"user:id:{user.user_id}", user_str)
        redis_client.set(f"user:username:{user.username}", user_str)
        redis_client.set(f"data:user:{user.user_id}", user_str)
        return user

    @staticmethod
    def update_status(curr_user: User, enabled: bool):
        user = User.query.filter(User.user_id == curr_user.user_id).one()
        if user is None or not user.user_id:
            raise AppException(f'修改的数据可能已不存在!')
        redis_client.delete(f"data:user:{user.user_id}")
        redis_client.delete(f"menu:user:{user.user_id}")
        redis_client.delete(f"role:auth:{user.user_id}")
        user.enabled = enabled
        user.update_by = curr_user.update_by
        user.update_time = datetime.datetime.now()
        db.session.commit()
        redis_client.delete(f"user:id:{user.user_id}")
        redis_client.delete(f"user:username:{user.username}")
        user_dict = marshal(user, user_edit_fields)
        user_str = json.dumps(user_dict, ensure_ascii=False)
        redis_client.set(f"user:id:{user.user_id}", user_str)
        redis_client.set(f"user:username:{user.username}", user_str)
        redis_client.set(f"data:user:{user.user_id}", user_str)
        return user

    @staticmethod
    def create(curr_user: User):
        exist_username = User.query.filter(User.username == curr_user.username).one_or_none()
        if exist_username and exist_username.user_id != curr_user.user_id:
            raise AppException(f'{curr_user.username}已存在！')
        exist_email = User.query.filter(User.email == curr_user.email).one_or_none()
        if exist_email and exist_email.user_id != curr_user.user_id:
            raise AppException(f'{curr_user.email}已存在！')

        user = User()
        user.username = curr_user.username
        user.nick_name = curr_user.nick_name
        user.email = curr_user.email
        user.phone = curr_user.phone
        user.gender = curr_user.gender
        user.password = curr_user.password
        user.enabled = curr_user.enabled
        user.create_by = curr_user.create_by
        user.create_time = datetime.datetime.now()
        user.dept_id = curr_user.dept_id
        user.dept = Dept.query.filter(Dept.dept_id == curr_user.dept.dept_id).one()
        user.roles = Role.query.filter(Role.role_id.in_([r.role_id for r in curr_user.roles])).all()
        user.jobs = Job.query.filter(Job.job_id.in_([j.job_id for j in curr_user.jobs])).all()
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            users = User.query.filter(User.user_id.in_(ids)).all()
            for user in users:
                redis_client.delete(f"user:id:{user.user_id}")
                redis_client.delete(f"user:username:{user.username}")
                for job in user.jobs:
                    user.jobs.remove(job)
                for role in user.roles:
                    user.roles.remove(role)
                db.session.delete(user)
            db.session.commit()

    @staticmethod
    def update_center(curr_user: dict):
        user = User.query.filter(User.user_id == curr_user["id"]).one()
        user.nick_name = curr_user["nickName"]
        user.phone = curr_user["phone"]
        user.gender = curr_user["gender"]
        user.update_time = datetime.datetime.now()
        db.session.commit()
        redis_client.delete(f"user:id:{user.user_id}")
        redis_client.delete(f"user:username:{user.username}")

    @staticmethod
    def update_pass(user: User, password: str):
        """
        更新密码
        :param user: 用户
        :param password: 密文
        """
        user = User.query.filter(User.user_id == user.user_id).one_or_none()
        if user is None:
            raise AppException(f'您所操作的对象已不存在!')
        user.password = password
        user.pwd_reset_time = datetime.datetime.now()
        db.session.commit()
        redis_client.delete(f"user:username:{user.username}")
        redis_client.delete(f"user:id:{user.user_id}")

    @staticmethod
    def update_avatar(user_id: int, file_path: str):
        user = User.query.filter(User.user_id == user_id).one_or_none()
        if user is None:
            raise AppException(f'您所操作的对象已不存在!')
        user.avatar_path = file_path
        user.avatar_name = os.path.basename(file_path)
        user.update_time = datetime.datetime.now()
        db.session.commit()
        redis_client.delete(f"user:username:{user.username}")
        redis_client.delete(f"user:id:{user.user_id}")

    @staticmethod
    def update_email(user_id: int, email: str):
        user = User.query.filter(User.user_id == user_id).one_or_none()
        if user is None:
            raise AppException(f'您所操作的对象已不存在!')
        user.email = email
        user.update_time = datetime.datetime.now()
        db.session.commit()
        redis_client.delete(f"user:username:{user.username}")
        redis_client.delete(f"user:id:{user.user_id}")

    @staticmethod
    def refresh_roles(user: User):
        # 刷新用户权限
        for token in redis_client.scan_iter(f'{ServerConfig.online_key}*'):
            user_cache = json.loads(redis_client.get(token))
            if user_cache["id"] == user.user_id:
                user_cache["roles"] = RoleService.map_to_granted_authorities(user=user)
                redis_client.set(token, json.dumps(user_cache, ensure_ascii=False))


class MenuService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs) -> list:
        blurry = kwargs.get('blurry')
        create_times = kwargs.get('createTime')
        pid = kwargs.get('pid')
        not_empty = blurry or pid or create_times
        pid_is_null = True if not not_empty else False
        query = []
        if blurry:
            query.append(or_(Menu.title.like(f'%{blurry}%'), Menu.component.like(f'%{blurry}%'),
                             Menu.permission.like(f'%{blurry}%')))
        if pid:
            query.append((Menu.pid == pid))
        if pid_is_null:
            query.append((Menu.pid.is_(None)))
        if create_times and len(create_times) >= 2:
            query.append((Menu.create_time.between(create_times[0], create_times[1])))
        return Menu.query.filter(*query).order_by(Menu.menu_sort).paginate(int(page) + 1, per_page=int(size),
                                                  error_out=False)

    @staticmethod
    def query_all_menus() -> list:
        key = 'menu:all'
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            cache_dict = json.loads(cache_str)
            schema = MenuSchema()
            all_menus = schema.load(cache_dict, unknown="exclude", many=True)
        else:
            all_menus = Menu.query.all()
            redis_client.set(key, json.dumps([marshal(m, menu_fields) for m in all_menus], ensure_ascii=False))
        return all_menus

    @staticmethod
    def get_menu_tree(menus):
        trees = []
        for m in menus:
            if m["pid"] is None:
                trees.append(m)
            for mc in menus:
                if mc['pid'] and mc['pid'] == m['id']:
                    if m.get("children") is None:
                        m['children'] = []
                    m['children'].append(mc)
        trees = [x for x in menus if x['pid'] is None] if len(trees) == 0 else trees
        rs = api_utils.build_menu_tree(trees)
        return rs

    @staticmethod
    # @cacheable('menu:user:#user_id')
    def find_by_user(user_id: int) -> list:
        key = f"menu:user:{user_id}"
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = MenuSchema()
            menus = schema.load(json.loads(cache_str), unknown="exclude", many=True)
        else:
            user = User.query.filter(User.user_id == user_id).one()
            menu_list = list(set([m for r in user.roles for m in r.menus]))
            menu_list.sort(key=lambda m: m.menu_sort)
            menus = list(filter(lambda x: x.type != 2, menu_list))
            menu_dict = marshal(menus, menu_fields)
            redis_client.set(key, json.dumps(menu_dict, ensure_ascii=False))
        return menus

    @staticmethod
    def find_by_id(menu_id: int) -> Menu:
        key = f"menu:id:{menu_id}"
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = MenuSchema()
            menu = schema.load(json.loads(cache_str), unknown="exclude")
        else:
            menu = db.session.query(Menu).filter(Menu.menu_id == menu_id).one_or_none()
            if menu is None:
                raise AppException(f'您所操作的对象已不存在!')
            menu_dict = marshal(menu, menu_fields)
            redis_client.set(key, json.dumps(menu_dict, ensure_ascii=False))
        return menu

    @staticmethod
    def get_superior(menu: Menu, menus: list, parent_dict: dict, menu_dict: dict) -> list:
        if menu.pid is None:
            parents = parent_dict[menu.pid]
            menus.extend(parents)
            return menus
        menus.extend(parent_dict[menu.pid])
        return MenuService.get_superior(menu_dict[menu.pid], menus, parent_dict, menu_dict)

    @staticmethod
    def get_menus(pid: int = 0) -> list:
        key = f'menu:pid:{pid}'
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = MenuSchema()
            menus = schema.load(json.loads(cache_str), unknown="exclude", many=True)
        else:
            if pid:
                menus = db.session.query(Menu).filter(Menu.pid == pid).all()
            else:
                menus = db.session.query(Menu).filter(Menu.pid.is_(None)).all()
            menu_dict = marshal(menus, menu_fields)
            redis_client.set(key, json.dumps(menu_dict, ensure_ascii=False))
        return menus

    @staticmethod
    def build_tree(menus_param: list) -> (int, list):
        trees = []
        ids = set()
        for d in menus_param:
            if d.pid is None:
                trees.append(d)
            for c in menus_param:
                if c.pid is not None and c.pid == d.menu_id:
                    if d.children is None:
                        d.children = []
                    d.children.append(c)
                    ids.add(c.menu_id)
        if len(trees) == 0:
            trees = [m for m in menus_param if m.menu_id not in ids]
        return trees

    @staticmethod
    def create(curr_menu: Menu):
        exist_title = Menu.query.filter(Menu.title == curr_menu.title).one_or_none()
        if exist_title:
            raise AppException(f"{curr_menu.title}已存在!")
        if curr_menu.name:
            exist_name = Menu.query.filter(Menu.name == curr_menu.name).one_or_none()
            if exist_name:
                raise AppException(f"{curr_menu.name}已存在!")
        if curr_menu.i_frame is True:
            http, https = "http://", "https://"
            if not curr_menu.path.lower().startswith(http) and not curr_menu.path.lower().startswith(https):
                raise AppException("外链必须以http://或者https://开头")
        curr_menu.create_time = datetime.datetime.now()
        if curr_menu.pid ==0:
            del curr_menu.pid
        db.session.add(curr_menu)
        db.session.commit()
        if curr_menu.pid:
            MenuService.update_sub_count(curr_menu.pid)
        redis_client.delete(f"menu:pid:{0 if curr_menu.pid is None else curr_menu.pid}")
        redis_client.delete('menu:all')

    @staticmethod
    def update_sub_count(menu_id: int):
        if menu_id:
            menu = Menu.query.filter(Menu.menu_id == menu_id).one_or_none()
            if menu:
                sub_count = db.session.query(func.count(Menu.menu_id)).filter(Menu.pid == menu_id).scalar()
                menu.sub_count = sub_count
                db.session.commit()

    @staticmethod
    def update(curr_menu: Menu):
        menu = Menu.query.filter(Menu.menu_id == curr_menu.menu_id).one_or_none()
        if menu is None:
            raise AppException(f'修改的数据可能已不存在!')
        new_pid = curr_menu.pid
        if new_pid and new_pid == curr_menu.menu_id:
            raise AppException("上级不能为自己")

        if curr_menu.i_frame is True:
            http, https = "http://", "https://"
            if not curr_menu.path.lower().startswith(http) and not curr_menu.path.lower().startswith(https):
                raise AppException("外链必须以http://或者https://开头")
        exist_title = Menu.query.filter(Menu.title == curr_menu.title).one_or_none()
        if exist_title and exist_title.menu_id != menu.menu_id:
            raise AppException(f"{menu.title}已存在!")

        if menu.name:
            exist_name = Menu.query.filter(Menu.name == menu.name).one_or_none()
            if exist_name and exist_name.menu_id != menu.menu_id:
                raise AppException(f"{menu.name}已存在!")
        pid = menu.pid
        menu.title = curr_menu.title
        menu.component = curr_menu.component
        menu.path = curr_menu.path
        menu.icon = curr_menu.icon
        menu.i_frame = curr_menu.i_frame
        menu.pid = curr_menu.pid if curr_menu.pid else None
        menu.menu_sort = curr_menu.menu_sort
        menu.cache = curr_menu.cache
        menu.hidden = curr_menu.hidden
        menu.name = curr_menu.name
        menu.permission = curr_menu.permission
        menu.type = curr_menu.type
        menu.update_time = datetime.datetime.now()
        db.session.commit()
        if menu.pid != pid:
            MenuService.update_sub_count(pid)
            MenuService.update_sub_count(menu.pid)
        MenuService.clear_cache(menu.menu_id, menu.pid)

    @staticmethod
    def clear_cache(menu_id: int, pid: int):
        redis_client.delete(f"menu:id:{menu_id}")
        redis_client.delete('menu:all')
        if pid:
            redis_client.delete(f"menu:pid:{pid}")
        for key in redis_client.scan_iter(f"menu:user:*"):
            redis_client.delete(key)

    @staticmethod
    def get_delete_menus(menu_list: list, menu_set: set):
        for menu in menu_list:
            menus = Menu.query.filter(Menu.pid == menu.menu_id).all()
            menu_set = menu_set | set(menus)
            if menus:
                MenuService.get_delete_menus(menus, menu_set)

    @staticmethod
    def delete(menu_set: set):
        if menu_set:
            for menu in menu_set:
                MenuService.clear_cache(menu.menu_id, menu.pid)
                db.session.delete(menu)
                if menu.roles:
                    for r in menu.roles:
                        menu.roles.remove(r)
                if menu.pid:
                    MenuService.update_sub_count(menu.pid)

            db.session.commit()


class DeptService:
    @staticmethod
    # @cacheable("pid:#dept_id")
    def find_by_pid(dept_id: int) -> list:
        key = f"dept:pid:{dept_id}"
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = DeptSchema()
            children = schema.load(json.loads(cache_str), unknown="exclude", many=True)
        else:
            children = db.session.query(Dept).filter(Dept.pid == dept_id).all()
            depts_dict = [marshal(d, dept_fields) for d in children]
            redis_client.set(key, json.dumps(depts_dict, ensure_ascii=False))
        return children

    @staticmethod
    def find_by_id(dept_id: int) -> Dept:
        key = f"dept:id:{dept_id}"
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = DeptSchema()
            dept = schema.load(json.loads(cache_str), unknown="exclude")
        else:
            dept = db.session.query(Dept).filter(Dept.dept_id == dept_id).one_or_none()
            if dept is None:
                raise AppException(f'您所操作的对象已不存在!')
            dept_dict = marshal(dept, dept_fields)
            redis_client.set(key, json.dumps(dept_dict, ensure_ascii=False))
        return dept

    @staticmethod
    def get_dept_children(dept_list: list) -> list:
        rs = []
        for dept in dept_list:
            if dept.enabled:
                children = DeptService.find_by_pid(dept_id=dept.dept_id)
                if children:
                    rs.extend(DeptService.get_dept_children(children))
                rs.append(dept.dept_id)
        return rs

    @staticmethod
    def get_superior(dept: Dept, depts: list) -> list:
        if dept.pid is None:
            # parents = db.session.query(Dept).filter(Dept.pid.is_(None)).all()
            parents = DeptService.find_by_pid(dept_id=dept.pid)
            depts.extend(parents)
            return depts
        depts.extend(DeptService.find_by_pid(dept_id=dept.pid))
        return DeptService.get_superior(DeptService.find_by_id(dept_id=dept.pid), depts)

    @staticmethod
    def build_tree(depts_param: list) -> (int, list):
        trees = set()
        depts = set()
        dept_names = [x.name for x in depts_param]
        for d in depts_param:
            is_child = False
            if d.pid is None:
                trees.add(d)
            for c in depts_param:
                if c.pid and c.pid == d.dept_id:
                    is_child = True
                    if d.children is None:
                        d.children = []
                    d.children.append(c)
            if is_child:
                depts.add(d)
            else:
                dept = None
                if d.pid:
                    dept = DeptService.find_by_id(d.pid)
                if dept and dept.name not in dept_names:
                    depts.add(d)
        if len(trees) == 0:
            trees = depts
        return len(depts_param), depts if len(trees) == 0 else trees

    @staticmethod
    def query_all(page=0, size=9999, **kwargs) -> list:
        name = kwargs.get('name')
        enabled = kwargs.get('enabled')
        pid = kwargs.get('pid')
        create_times = kwargs.get('createTime')
        not_empty = name or pid or create_times
        pid_is_null = True if not not_empty else False
        pid = kwargs.get('pid')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, dept_fields, Dept)
        query = []
        if name:
            query.append((Dept.name.like(f'%{name}%')))
        if enabled:
            query.append((Dept.enabled.is_(True if enabled == 'true' else False)))
        if pid:
            query.append((Dept.pid == pid))
        if pid_is_null:
            query.append((Dept.pid.is_(None)))
        if create_times and len(create_times) >= 2:
            query.append((Dept.create_time.between(create_times[0], create_times[1])))
        return Dept.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                         error_out=False)

    @staticmethod
    def query_all_depts() -> list:
        key = 'dept:all'
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            cache_dict = json.loads(cache_str)
            schema = DeptSchema()
            all_depts = schema.load(cache_dict, unknown="exclude", many=True)
        else:
            all_depts = Dept.query.all()
            redis_client.set(key, json.dumps([marshal(d, dept_fields) for d in all_depts], ensure_ascii=False))
        return all_depts

    @staticmethod
    def create(curr_dept: Dept):
        curr_dept.create_time = datetime.datetime.now()
        db.session.add(curr_dept)
        db.session.commit()
        if curr_dept.pid:
            redis_client.delete(f"dept:pid:{curr_dept.pid}")
            redis_client.delete("dept:all")
            DeptService.update_sub_count(curr_dept.pid)

    @staticmethod
    def update(curr_dept: Dept):
        dept = Dept.query.filter(Dept.dept_id == curr_dept.dept_id).one_or_none()
        if dept is None:
            raise AppException(f'修改的数据可能已不存在!')
        new_pid = curr_dept.pid
        if new_pid and new_pid == curr_dept.dept_id:
            raise AppException("上级不能为自己")
        pid = dept.pid
        dept.name = curr_dept.name
        dept.pid = curr_dept.pid
        dept.dept_sort = curr_dept.dept_sort
        dept.enabled = curr_dept.enabled
        dept.update_time = datetime.datetime.now()
        db.session.commit()
        DeptService.clear_cache(dept.dept_id, dept.pid, pid)
        if dept.pid != pid:
            DeptService.update_sub_count(pid)
            DeptService.update_sub_count(dept.pid)

    @staticmethod
    def update_sub_count(dept_id: int):
        if dept_id:
            dept = Dept.query.filter(Dept.dept_id == dept_id).one_or_none()
            if dept:
                sub_count = db.session.query(func.count(Dept.dept_id)).filter(Dept.pid == dept_id).scalar()
                dept.sub_count = sub_count
                db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            dept_set = DeptService.get_children_by_ids(ids=ids)
            db.session.query(Dept).filter(Dept.dept_id.in_(ids)).delete(synchronize_session=False)
            for dept in dept_set:
                DeptService.clear_cache(dept.dept_id, dept.pid, 0)
                if dept.pid:
                    DeptService.update_sub_count(dept.pid)

            db.session.commit()

    @staticmethod
    def clear_cache(dept_id: int, pid: int, old_pid: int):
        for key in redis_client.scan_iter('data:user:*'):
            redis_client.delete(key)
        redis_client.delete("dept:all")
        redis_client.delete(f"dept:id:{dept_id}")
        if pid:
            redis_client.delete(f"dept:pid:{pid}")
        if old_pid:
            redis_client.delete(f"dept:pid:{old_pid}")

    @staticmethod
    def get_children_by_ids(ids: list) -> set:
        dept_set = set()
        for dept_id in ids:
            depts = Dept.query.filter(Dept.pid == dept_id).all()
            dept_set.add(Dept.query.filter(Dept.dept_id == dept_id).one())
            if depts:
                DeptService.get_delete_depts(depts, dept_set)
        return dept_set

    @staticmethod
    def get_delete_depts(dept_list: list, dept_set: set):
        for dept in dept_list:
            depts = Dept.query.filter(Dept.pid == dept.dept_id).all()
            dept_set.update(set(depts))
            if depts:
                DeptService.get_delete_depts(depts, dept_set)

    @staticmethod
    def verification(dept_set: set):
        dept_ids = [dept.dept_id for dept in dept_set]
        user_count = db.session.query(func.count(User.user_id)).filter(User.dept_id.in_(dept_ids)).scalar()
        if user_count > 0:
            raise AppException("所选部门存在用户关联，请解除后再试!")
        depts = db.session.query(Dept).filter(Dept.dept_id.in_(dept_ids)).all()
        for d in depts:
            if d.roles.all():
                raise AppException("所选部门存在角色关联，请解除后再试!")


class DataService:
    @staticmethod
    def get_dept_ids(user: User) -> list:
        key = f'data:user:{user.user_id}'
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            dept_ids = json.loads(cache_str)
        else:
            dept_ids = set()
            for role in user.roles.all():
                if role.data_scope == '本级':
                    dept_ids.add(user.dept_id)
                elif role.data_scope == '自定义':
                    dept_ids.update(DataService.get_customize(dept_ids, role))
            redis_client.set(key, json.dumps(list(dept_ids), ensure_ascii=False))
        return list(dept_ids)

    @staticmethod
    def get_customize(dept_ids: set, role: Role) -> set:
        role = Role.query.filter(Role.role_id == role.role_id).one_or_none()
        if role:
            for dept in role.depts:
                dept_ids.add(dept.dept_id)
                dept_children = DeptService.find_by_pid(dept_id=dept.dept_id)
                if dept_children:
                    dept_ids.union(set(DeptService.get_dept_children(dept_children)))
        return dept_ids


class RoleService:
    @staticmethod
    def map_to_granted_authorities(user: User) -> list:
        # redis 中取出来的无DB上下文
        user = User.query.filter(User.user_id == user.user_id).one()
        key = f'role:auth:{user.user_id}'
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            permissions = json.loads(cache_str)
        else:
            permissions = set()
            if (type(user.is_admin) == bool and user.is_admin) or (
                    type(user.is_admin) != bool and user.is_admin[0] == 1):
                # 是管理员直接返回
                permissions.add("admin")
                return list(permissions)
            permissions = list(set([m.permission for r in user.roles for m in r.menus if m.permission]))
            redis_client.set(key, json.dumps(list(permissions), ensure_ascii=False))
        return list(permissions)

    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        blurry = kwargs.get('blurry')
        create_times = kwargs.get('createTime')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, role_edit_fields, Role)
        query = []
        if blurry:
            query.append(or_(Role.name.like(f'%{blurry}%'), Role.description.like(f'%{blurry}%')))
        if create_times and len(create_times) >= 2:
            query.append((Role.create_time.between(create_times[0], create_times[1])))
        return Role.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                         error_out=False)

    @staticmethod
    def query_all_roles():
        key = 'role:all'
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            roles_dict = json.loads(cache_str)
        else:
            roles = db.session.query(Role).order_by(Role.level.asc()).all()
            roles_dict = [marshal(r, role_fields) for r in roles]
            redis_client.set(key, json.dumps(roles_dict, ensure_ascii=False))
        return roles_dict

    @staticmethod
    def get_levels(user_id: int, level: int = None) -> int:
        roles = Role.query.join(UsersRoles).join(User).filter(User.user_id == user_id).all()
        min_level = min([x.level for x in roles])
        if level and level < min_level:
            raise AppException(f'权限不足，你的角色级别：{min}，低于操作的角色级别：{level}')
        return min_level

    @staticmethod
    def verification(ids: list):
        total = db.session.query(func.count(User.user_id)).join(UsersRoles).join(Role).filter(
            Role.role_id.in_(ids)).scalar()
        if total > 0:
            raise AppException("所选角色存在用户关联，请解除关联再试!")

    @staticmethod
    def find_by_id(role_id: int = None) -> Role:
        key = f"role:id:{role_id}"
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = RoleSchema()
            role = schema.load(json.loads(cache_str), unknown="exclude")
        else:
            role = Role.query.filter(Role.role_id == role_id).one_or_none()
            if role is None:
                raise AppException(f'您所操作的对象已不存在!')
            role_dict = marshal(role, role_edit_fields)
            redis_client.set(key, json.dumps(role_dict, ensure_ascii=False))
        return role

    @staticmethod
    def clear_cache():
        # users = User.query.join(UsersRoles).join(Role).filter(Role.role_id == role_id).all()
        # for user in users:
        redis_client.delete("role:all")
        api_utils.batch_clear("data:user:*")
        api_utils.batch_clear("menu:user:*")
        api_utils.batch_clear("role:auth:*")

    @staticmethod
    def update_menu(params: dict, role: Role):
        role = Role.query.filter(Role.role_id == role.role_id).one()
        role.menus = Menu.query.filter(Menu.menu_id.in_([d["id"] for d in params["menus"] if "id" in d])).all()
        db.session.commit()
        # users = User.query.join(UsersRoles).join(Role).filter(Role.role_id == role.role_id).all()
        # for user in users:
        #     redis_client.delete(f"menu:user:{user.user_id}")
        api_utils.batch_clear("menu:user:*")
        api_utils.batch_clear("role:auth:*")
        redis_client.delete(f"role:id:{role.role_id}")

    @staticmethod
    def create(curr_role: Role):
        curr_role.create_time = datetime.datetime.now()
        db.session.add(curr_role)
        db.session.commit()
        redis_client.delete("role:all")

    @staticmethod
    def update(curr_role: Role):
        role = Role.query.filter(Role.role_id == curr_role.role_id).one_or_none()
        if role is None:
            raise AppException(f'修改的数据可能已不存在!')
        role.name = curr_role.name
        role.level = curr_role.level
        role.description = curr_role.description
        role.data_scope = curr_role.data_scope
        role.update_by = curr_role.update_by
        role.update_time = datetime.datetime.now()
        db.session.commit()
        RoleService.clear_cache()

    @staticmethod
    def delete(ids: list):
        if ids:
            roles = Role.query.filter(Role.role_id.in_(ids)).all()
            for role in roles:
                RoleService.clear_cache()
                for dept in role.depts:
                    role.depts.remove(dept)
                for menu in role.menus:
                    role.menus.remove(menu)
                db.session.delete(role)
            db.session.commit()


class DictDetailService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        dict_name = kwargs.get('dictName')
        query = []
        if dict_name:
            query.append((Dict.name == dict_name))
        return DictDetail.query.join(Dict).filter(*query).paginate(int(page) + 1, per_page=int(size),
                                                                   error_out=False)

    @staticmethod
    def find_by_name(name: str):
        key = f'dict:name:{name}'
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            cache_dict = json.loads(cache_str)
            schema = DictSchema()
            datas = schema.load(cache_dict, unknown="exclude", many=True)
        else:
            datas = DictDetail.query.join(Dict).filter(Dict.name == name).all()
            data_dict = [marshal(d, dict_detail_fields) for d in datas]
            redis_client.set(key, json.dumps(data_dict, ensure_ascii=False))
        return datas

    @staticmethod
    def find_by_id(detail_id: int):
        data = DictDetail.query.join(Dict).filter(DictDetail.detail_id == detail_id).one_or_none()
        if data is None:
            raise AppException(f'您所操作的对象已不存在!')
        return data

    @staticmethod
    def create(curr_detail: DictDetail):
        curr_detail.create_time = datetime.datetime.now()
        db.session.add(curr_detail)
        db.session.commit()
        DictDetailService.clear_cache()

    @staticmethod
    def update(curr_detail: DictDetail):
        old_detail = DictDetail.query.filter(DictDetail.detail_id == curr_detail.detail_id).one_or_none()
        if old_detail is None:
            raise AppException(f'修改的数据可能已不存在!')
        old_detail.label = curr_detail.label
        old_detail.value = curr_detail.value
        old_detail.dict_sort = curr_detail.dict_sort
        old_detail.update_by = curr_detail.update_by
        old_detail.update_time = datetime.datetime.now()
        db.session.commit()
        DictDetailService.clear_cache()

    @staticmethod
    def delete(id_: int):
        if id_:
            db.session.query(DictDetail).filter(DictDetail.detail_id == id_).delete(synchronize_session=False)
            db.session.commit()
            DictDetailService.clear_cache()

    @staticmethod
    def clear_cache():
        for key in redis_client.scan_iter("dict:*"):
            redis_client.delete(key)
        for key in redis_client.scan_iter("detail:*"):
            redis_client.delete(key)


class JobService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, job_fields, Job)
        name = kwargs.get('name')
        enabled = kwargs.get('enabled')
        create_times = kwargs.get('createTime')
        query = []
        if name:
            query.append((Job.name.like(f'%{name}%')))
        if enabled:
            query.append((Job.enabled.is_(True if enabled == 'true' else False)))
        if create_times and len(create_times) >= 2:
            query.append((Job.create_time.between(create_times[0], create_times[1])))
        return Job.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                        error_out=False)

    @staticmethod
    def create(curr_job: Job):
        same_name_count = db.session.query(func.count(Job.job_id)).filter(Job.name == curr_job.name).scalar()
        if same_name_count > 0:
            raise AppException(f'{curr_job.name}已存在!')
        curr_job.create_time = datetime.datetime.now()
        db.session.add(curr_job)
        db.session.commit()

    @staticmethod
    def update(curr_job: Job):
        jobs = Job.query.filter(Job.name == curr_job.name).all()
        if [old for old in jobs if old.job_id != curr_job.job_id]:
            raise AppException(f'{curr_job.name}已存在!')
        job = Job.query.filter(Job.job_id == curr_job.job_id).one_or_none()
        if job is None:
            raise AppException(f'修改的数据可能已不存在!')
        job.name = curr_job.name
        job.job_sort = curr_job.job_sort
        job.enabled = curr_job.enabled
        job.update_time = datetime.datetime.now()
        job.update_by = curr_job.update_by
        db.session.commit()
        key = f"job:id:{job.job_id}"
        data_dict = marshal(job, job_fields)
        redis_client.set(key, json.dumps(data_dict, ensure_ascii=False))

    @staticmethod
    def delete(ids: list):
        if ids:
            db.session.query(Job).filter(Job.job_id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()
            for _id in ids:
                redis_client.delete(f"job:id:{_id}")

    @staticmethod
    def find_by_id(job_id: int = None) -> Role:
        key = f"job:id:{job_id}"
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = JobSchema()
            data = schema.load(json.loads(cache_str), unknown="exclude")
        else:
            data = Job.query.filter(Job.job_id == job_id).one_or_none()
            if data is None:
                raise AppException(f'您所操作的对象已不存在!')
            data_dict = marshal(data, job_fields)
            redis_client.set(key, json.dumps(data_dict, ensure_ascii=False))
        return data


class DictService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        blurry = kwargs.get('blurry')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, dict_fields, Dict)
        query = []
        if blurry:
            query.append(or_(Dict.name.like(f'%{blurry}%'), Dict.description.like(f'%{blurry}%')))
        return Dict.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                         error_out=False)

    @staticmethod
    def create(curr_dict: Dict):
        same_name_count = db.session.query(func.count(Dict.dict_id)).filter(Dict.name == curr_dict.name).scalar()
        if same_name_count > 0:
            raise AppException(f'{curr_dict.name}已存在!')
        curr_dict.create_by = curr_dict.create_by
        curr_dict.create_time = datetime.datetime.now()
        db.session.add(curr_dict)
        db.session.commit()
        DictService.clear_cache()

    @staticmethod
    def update(curr_dict: Dict):
        dicts = Dict.query.filter(Dict.name == curr_dict.name).all()
        if [old for old in dicts if old.dict_id != curr_dict.dict_id]:
            raise AppException(f'{curr_dict.name}已存在!')
        old_dict = Dict.query.filter(Dict.dict_id == curr_dict.dict_id).one_or_none()
        if old_dict is None:
            raise AppException(f'修改的数据可能已不存在!')
        old_dict.name = curr_dict.name
        old_dict.description = curr_dict.description
        old_dict.update_time = datetime.datetime.now()
        old_dict.update_by = curr_dict.update_by
        db.session.commit()
        DictService.clear_cache()

    @staticmethod
    def delete(ids: list):
        if ids:
            dict_list = db.session.query(Dict).filter(Dict.dict_id.in_(ids)).all()
            for d in dict_list:
                for detail in d.details:
                    d.details.remove(detail)
                db.session.delete(d)
            db.session.commit()
            DictService.clear_cache()

    @staticmethod
    def find_by_id(dict_id: int = None) -> Role:
        key = f"dict:id:{dict_id}"
        if redis_client.exists(key):
            cache_str = redis_client.get(key)
            schema = DictSchema()
            data = schema.load(json.loads(cache_str), unknown="exclude")
        else:
            data = Dict.query.filter(Dict.dict_id == dict_id).one_or_none()
            if data is None:
                raise AppException(f'您所操作的对象已不存在!')
            data_dict = marshal(data, dict_fields)
            redis_client.set(key, json.dumps(data_dict, ensure_ascii=False))
        return data

    @staticmethod
    def clear_cache():
        for key in redis_client.scan_iter(f"dict:*"):
            redis_client.delete(key)


class LogService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, logs_fields, Logs)
        blurry = kwargs.get('blurry')
        log_type = kwargs.get('logType')
        create_times = kwargs.get('createTime')
        query = []
        if blurry:
            query.append(or_(Logs.username.like(f'%{blurry}%'), Logs.description.like(f'%{blurry}%'),
                             Logs.address.like(f'%{blurry}%'), Logs.request_ip.like(f'%{blurry}%'),
                             Logs.method.like(f'%{blurry}%'), Logs.params.like(f'%{blurry}%')))
        if log_type:
            query.append((Logs.log_type == log_type))
        if create_times and len(create_times) >= 2:
            query.append((Logs.create_time.between(create_times[0], create_times[1])))
        return Logs.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                         error_out=False)

    @staticmethod
    def find_by_err_detail(_id: int):
        rs = Logs.query.filter(Logs.log_id == _id).one_or_none()
        if rs is None:
            raise AppException("查看的数据已不存在!")
        return rs

    @staticmethod
    def del_all_by_error():
        db.session.query(Logs).filter(Logs.log_type == 'ERROR').delete(synchronize_session=False)
        db.session.commit()

    @staticmethod
    def del_all_by_info():
        db.session.query(Logs).filter(Logs.log_type == 'INFO').delete(synchronize_session=False)
        db.session.commit()

    @staticmethod
    def save(log_model: Logs):
        db.session.add(log_model)
        db.session.commit()


class VerifyService:
    @staticmethod
    def send_email(email: str, prefix: str):
        key = f'{prefix}{email}'
        old_code = redis_client.get(key)
        if old_code is None:
            old_code = "".join(random_code())
            redis_client.set(key, old_code)
            redis_client.expire(key, datetime.timedelta(minutes=ServerConfig.code_expiration))
        email_info = {"receivers": [email], "subject": "EL-ADMIN后台管理系统", "content": ""}
        return old_code, email_info
