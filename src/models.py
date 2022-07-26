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

# @Time    : 2022/5/15 20:49
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : models.py
# @Project : eladmin_py_backend
import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import reconstructor
from sqlalchemy.sql import expression

from src.extensions import RedisClient

db = SQLAlchemy()
# redis_client = Cache()
redis_client = RedisClient()


class Base(db.Model):
    __abstract__ = True
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    create_by = db.Column(db.String())
    update_by = db.Column(db.String())
    create_time = db.Column(db.DateTime(), default=datetime.datetime.now())
    update_time = db.Column(db.DateTime(), onupdate=datetime.datetime.now)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)


UsersRoles = db.Table('sys_users_roles', db.metadata,
                      db.Column('user_id', db.BigInteger,
                                db.ForeignKey('sys_user.user_id', onupdate="CASCADE", ondelete="CASCADE"),
                                primary_key=True),
                      db.Column('role_id', db.BigInteger,
                                db.ForeignKey('sys_role.role_id', onupdate="CASCADE", ondelete="CASCADE"),
                                primary_key=True),
                      )
UsersJobs = db.Table('sys_users_jobs', db.metadata,
                     db.Column('user_id', db.BigInteger,
                               db.ForeignKey('sys_user.user_id', onupdate="CASCADE", ondelete="CASCADE"),
                               primary_key=True),
                     db.Column('job_id', db.BigInteger,
                               db.ForeignKey('sys_job.job_id', onupdate="CASCADE", ondelete="CASCADE"),
                               primary_key=True)
                     )
RolesDepts = db.Table('sys_roles_depts', db.metadata,
                      db.Column('role_id', db.BigInteger,
                                db.ForeignKey('sys_role.role_id', onupdate="CASCADE", ondelete="CASCADE"),
                                primary_key=True),
                      db.Column('dept_id', db.BigInteger,
                                db.ForeignKey('sys_dept.dept_id', onupdate="CASCADE", ondelete="CASCADE"),
                                primary_key=True)
                      )
RolesMenus = db.Table('sys_roles_menus', db.metadata,
                      db.Column('role_id', db.BigInteger,
                                db.ForeignKey('sys_role.role_id', onupdate="CASCADE", ondelete="CASCADE"),
                                primary_key=True),
                      db.Column('menu_id', db.BigInteger,
                                db.ForeignKey('sys_menu.menu_id', onupdate="CASCADE", ondelete="CASCADE"),
                                primary_key=True)
                      )
DeployServer = db.Table('mnt_deploy_server', db.metadata,
                        db.Column('deploy_id', db.BigInteger,
                                  db.ForeignKey('mnt_deploy.deploy_id', onupdate="CASCADE", ondelete="CASCADE"),
                                  primary_key=True),
                        db.Column('server_id', db.BigInteger,
                                  db.ForeignKey('mnt_server.server_id', onupdate="CASCADE", ondelete="CASCADE"),
                                  primary_key=True)
                        )


class User(Base):
    __tablename__ = "sys_user"
    user_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    username = db.Column(db.String(), nullable=False, unique=True, index=True)
    nick_name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(), nullable=False)
    gender = db.Column(db.String())
    avatar_name = db.Column(db.String(), index=True)
    avatar_path = db.Column(db.String())
    password = db.Column(db.String())
    enabled = db.Column(db.Boolean(), index=True)
    pwd_reset_time = db.Column(db.DateTime())
    is_admin = db.Column(db.Integer(), server_default=expression.false(), default=False)
    # ForeignKey中是表名.字段名
    dept_id = db.Column(db.BigInteger(), db.ForeignKey('sys_dept.dept_id'), index=True)
    # roles = db.relationship('Role', secondary=UsersRoles, lazy='dynamic')
    # cascade='all, delete, delete-orphan', single_parent=True会删除关联表及对应表数据
    roles = db.relationship('Role', secondary=UsersRoles, back_populates='users', lazy='dynamic')
    # user_roles = association_proxy('roles', 'sys_role')
    # jobs = db.relationship('Job', secondary=UsersJobs, lazy='dynamic')
    jobs = db.relationship('Job', secondary=UsersJobs, back_populates='users', lazy='dynamic')
    # Dept不是字段,只是关系,backref是反向关联的关键字
    # dept = db.relationship('Dept', backref=db.backref('User', uselist=False, lazy='select'))
    dept = db.relationship('Dept', back_populates='user')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<User %r>' % self.user_id

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.user_id) + hash(self.user_id)


class Dept(Base):
    __tablename__ = "sys_dept"
    dept_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    pid = db.Column(db.BigInteger(), index=True)
    sub_count = db.Column(db.Integer())
    name = db.Column(db.String(), nullable=False)
    dept_sort = db.Column(db.Integer())
    enabled = db.Column(db.Integer(), server_default=expression.false(), default=False, nullable=False, index=True)
    # roles = db.relationship('Role', secondary=RolesDepts,
    #                         backref=db.backref('depts', lazy='dynamic'), lazy='dynamic')
    roles = db.relationship('Role', secondary=RolesDepts, back_populates='depts', lazy='dynamic')
    user = db.relationship('User', uselist=False, back_populates='dept')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children = []

    @reconstructor
    def init_db_load(self):
        self.children = []

    def __repr__(self):
        return '<Dept %r>' % self.dept_id

    def __eq__(self, other):
        if isinstance(other, Dept):
            return self.dept_id == other.dept_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.dept_id) + hash(self.dept_id)


class Job(Base):
    __tablename__ = "sys_job"
    job_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    name = db.Column(db.String(), nullable=False, unique=True, index=True)
    enabled = db.Column(db.Integer(), server_default=expression.false(), default=False, nullable=False, index=True)
    job_sort = db.Column(db.Integer(), nullable=False)
    users = db.relationship("User", secondary=UsersJobs, back_populates="jobs")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<Job %r>' % self.job_id

    def __eq__(self, other):
        if isinstance(other, Job):
            return self.job_id == other.job_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.job_id) + hash(self.job_id)


class DictDetail(Base):
    __tablename__ = "sys_dict_detail"
    detail_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, nullable=False, unique=True,
                          index=True)
    dict_id = db.Column(db.BigInteger(), db.ForeignKey('sys_dict.dict_id', ondelete='CASCADE'), index=True)
    label = db.Column(db.String(), nullable=False)
    value = db.Column(db.String(), nullable=False)
    dict_sort = db.Column(db.Integer(), nullable=False)
    dict_ = db.relationship('Dict', back_populates='details')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<DictDetail %r>' % self.detail_id

    def __eq__(self, other):
        if isinstance(other, DictDetail):
            return self.detail_id == other.detail_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.detail_id) + hash(self.detail_id)


class Dict(Base):
    __tablename__ = "sys_dict"
    dict_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String())
    details = db.relationship('DictDetail', back_populates='dict_', cascade='all, delete, delete-orphan',
                              single_parent=True, passive_deletes=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<Dict %r>' % self.dict_id

    def __eq__(self, other):
        if isinstance(other, Dict):
            return self.dict_id == other.dict_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.dict_id) + hash(self.dict_id)


class Menu(Base):
    __tablename__ = "sys_menu"
    menu_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    pid = db.Column(db.BigInteger(), index=True)
    sub_count = db.Column(db.Integer())
    type = db.Column(db.Integer())
    title = db.Column(db.String(), nullable=False, unique=True, index=True)
    name = db.Column(db.String(), unique=True, index=True)
    component = db.Column(db.String())
    menu_sort = db.Column(db.Integer())
    icon = db.Column(db.String())
    path = db.Column(db.String())
    i_frame = db.Column(db.Integer())
    cache = db.Column(db.Integer(), server_default=expression.false(), default=False)
    hidden = db.Column(db.Integer(), server_default=expression.false(), default=False)
    permission = db.Column(db.String())
    roles = db.relationship("Role", secondary=RolesMenus, back_populates='menus', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children = []

    @reconstructor
    def init_db_load(self):
        self.children = []

    def __repr__(self):
        return '<Menu %r>' % self.menu_id

    def __eq__(self, other):
        if isinstance(other, Menu):
            return self.menu_id == other.menu_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.menu_id) + hash(self.menu_id)


class Role(Base):
    __tablename__ = "sys_role"
    # keyword = db.Column('sys_role', db.String())  # User.association_proxy时使用
    role_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    name = db.Column(db.String(), nullable=False, unique=True, index=True)
    level = db.Column(db.Integer())
    description = db.Column(db.String())
    data_scope = db.Column(db.String())
    # menus = db.relationship('Menu', secondary=RolesMenus,
    #                         backref=db.backref('roles', lazy='dynamic'), lazy='dynamic')
    menus = db.relationship("Menu", secondary=RolesMenus, back_populates='roles', lazy='dynamic')
    depts = db.relationship("Dept", secondary=RolesDepts, back_populates='roles', lazy='dynamic')
    users = db.relationship("User", secondary=UsersRoles, back_populates="roles", lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<Role %r>' % self.role_id

    def __eq__(self, other):
        if isinstance(other, Role):
            return self.role_id == other.role_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.role_id) + hash(self.role_id)


class QuartzJob(Base):
    __tablename__ = "sys_quartz_job"
    job_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    bean_name = db.Column(db.String())
    cron_expression = db.Column(db.String())
    is_pause = db.Column(db.Integer(), server_default=expression.false(), default=False)
    job_name = db.Column(db.String())
    method_name = db.Column(db.String())
    params = db.Column(db.String())
    description = db.Column(db.String())
    person_in_charge = db.Column(db.String())
    email = db.Column(db.String())
    sub_task = db.Column(db.String())
    pause_after_failure = db.Column(db.Integer(), server_default=expression.false(), default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.uuid = None

    @reconstructor
    def init_db_load(self):
        self.uuid = None

    def __repr__(self):
        return '<QuartzJob %r>' % self.job_id

    def __eq__(self, other):
        if isinstance(other, QuartzJob):
            return self.job_id == other.job_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.job_id) + hash(self.job_id)


class QuartzLog(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "sys_quartz_log"
    log_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    bean_name = db.Column(db.String())
    cron_expression = db.Column(db.String())
    exception_detail = db.Column(db.String())
    is_success = db.Column(db.Integer(), server_default=expression.false(), default=False)
    job_name = db.Column(db.String())
    method_name = db.Column(db.String())
    params = db.Column(db.String())
    log_time = db.Column('time', db.BigInteger())
    create_time = db.Column(db.DateTime(), default=datetime.datetime.now())

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)

    def __repr__(self):
        return '<QuartzLog %r>' % self.log_id

    def __eq__(self, other):
        if isinstance(other, QuartzLog):
            return self.log_id == other.log_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.log_id) + hash(self.log_id)


class Logs(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "sys_log"
    log_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    description = db.Column(db.String())
    log_type = db.Column(db.String(), index=True)
    method = db.Column(db.String())
    params = db.Column(db.String())
    request_ip = db.Column(db.String())
    log_time = db.Column('time', db.Integer())
    username = db.Column(db.String())
    address = db.Column(db.String())
    browser = db.Column(db.String())
    exception_detail = db.Column(db.String())
    create_time = db.Column(db.DateTime(), default=datetime.datetime.now())

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<Logs %r>' % self.log_id

    def __eq__(self, other):
        if isinstance(other, Logs):
            return self.log_id == other.log_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.log_id) + hash(self.log_id)


class MntServer(Base):
    __tablename__ = "mnt_server"
    server_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    account = db.Column(db.String())
    ip = db.Column(db.String(), index=True)
    name = db.Column(db.String())
    password = db.Column(db.String())
    port = db.Column(db.Integer())
    dps = db.relationship("MntDeploy", secondary=DeployServer, back_populates="deploys")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<MntServer %r>' % self.server_id

    def __eq__(self, other):
        if isinstance(other, MntServer):
            return self.server_id == other.server_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.server_id) + hash(self.server_id)


class MntDeploy(Base):
    __tablename__ = "mnt_deploy"
    deploy_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    app_id = db.Column(db.BigInteger(), db.ForeignKey('mnt_app.app_id', ondelete='CASCADE'), index=True)
    deploys = db.relationship('MntServer', secondary=DeployServer, back_populates="dps", lazy='dynamic')
    app = db.relationship('MntApp', back_populates='deploy')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.servers = []

    @reconstructor
    def init_db_load(self):
        self.servers = []

    def __repr__(self):
        return '<MntDeploy %r>' % self.deploy_id

    def __eq__(self, other):
        if isinstance(other, MntDeploy):
            return self.deploy_id == other.deploy_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.deploy_id) + hash(self.deploy_id)


class MntApp(Base):
    __tablename__ = "mnt_app"
    app_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    name = db.Column(db.String())
    upload_path = db.Column(db.String())
    deploy_path = db.Column(db.String())
    backup_path = db.Column(db.String())
    port = db.Column(db.Integer())
    start_script = db.Column(db.String())
    deploy_script = db.Column(db.String())
    deploy = db.relationship('MntDeploy', back_populates='app', uselist=False, cascade='all, delete, delete-orphan',
                             single_parent=True, passive_deletes=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<MntApp %r>' % self.app_id

    def __eq__(self, other):
        if isinstance(other, MntApp):
            return self.app_id == other.app_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.app_id) + hash(self.app_id)


class MntDeployHistory(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "mnt_deploy_history"
    history_id = db.Column(db.String(), primary_key=True, autoincrement=False, unique=True, index=True)
    app_name = db.Column(db.String())
    deploy_date = db.Column(db.DateTime())
    deploy_user = db.Column(db.String())
    ip = db.Column(db.String())
    deploy_id = db.Column(db.BigInteger())

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<MntDeployHistory %r>' % self.history_id

    def __eq__(self, other):
        if isinstance(other, MntDeployHistory):
            return self.history_id == other.history_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.history_id) + hash(self.history_id)


class MntDatabase(Base):
    __tablename__ = "mnt_database"
    db_id = db.Column(db.String(), primary_key=True, autoincrement=False, unique=True, index=True)
    name = db.Column(db.String())
    jdbc_url = db.Column(db.String())
    user_name = db.Column(db.String())
    pwd = db.Column(db.String())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return '<MntDatabase %r>' % self.db_id

    def __eq__(self, other):
        if isinstance(other, MntDatabase):
            return self.db_id == other.db_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.db_id) + hash(self.db_id)


class CodeGenConfig(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "code_gen_config"
    config_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    table_name = db.Column(db.String(), index=True)
    author = db.Column(db.String())
    cover = db.Column(db.Integer(), server_default=expression.false(), default=False)
    module_name = db.Column(db.String())
    pack = db.Column(db.String())
    path = db.Column(db.String())
    api_path = db.Column(db.String())
    prefix = db.Column(db.String())
    api_alias = db.Column(db.String())

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<CodeGenConfig %r>' % self.config_id

    def __eq__(self, other):
        if isinstance(other, CodeGenConfig):
            return self.config_id == other.config_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.config_id) + hash(self.config_id)


class CodeColumnConfig(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "code_column_config"
    column_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    table_name = db.Column(db.String(), index=True)
    column_name = db.Column(db.String())
    column_type = db.Column(db.String())
    dict_name = db.Column(db.String())
    extra = db.Column(db.String())
    form_show = db.Column(db.Integer(), server_default=expression.false(), default=False)
    form_type = db.Column(db.String())
    key_type = db.Column(db.String())
    list_show = db.Column(db.Integer(), server_default=expression.false(), default=False)
    not_null = db.Column(db.Integer(), server_default=expression.false(), default=False)
    query_type = db.Column(db.String())
    remark = db.Column(db.String())
    date_annotation = db.Column(db.String())

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<CodeColumnConfig %r>' % self.column_id

    def __eq__(self, other):
        if isinstance(other, CodeColumnConfig):
            return self.column_id == other.column_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.column_id) + hash(self.column_id)


class ToolAlipayConfig(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "tool_alipay_config"
    config_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    app_id = db.Column(db.String())  # 应用ID
    charset = db.Column(db.String(), server_default="utf-8")  # 编码
    format = db.Column(db.String(), server_default="JSON")  # 类型 固定格式json
    gateway_url = db.Column(db.String(), server_default=r"https://openapi.alipaydev.com/gateway.do")  # 网关地址
    notify_url = db.Column(db.String())  # 异步回调
    private_key = db.Column(db.String())  # 私钥
    public_key = db.Column(db.String())  # 公钥
    return_url = db.Column(db.String())  # 回调地址
    sign_type = db.Column(db.String())  # 签名方式
    sys_service_provider_id = db.Column(db.String(), server_default="RSA2")  # 商户号

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<ToolAlipayConfig %r>' % self.config_id

    def __eq__(self, other):
        if isinstance(other, ToolAlipayConfig):
            return self.config_id == other.config_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.config_id) + hash(self.config_id)


class ToolEmailConfig(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "tool_email_config"
    config_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    from_user = db.Column(db.String(), nullable=False)  # 收件人
    host = db.Column(db.String(), nullable=False)  # 邮件服务器smtp地址
    password = db.Column('pass', db.String(), nullable=False)  # 密码
    port = db.Column(db.String(), nullable=False)  # 端口
    user = db.Column(db.String(), nullable=False)  # 发件者用户名

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<ToolEmailConfig %r>' % self.config_id

    def __eq__(self, other):
        if isinstance(other, ToolEmailConfig):
            return self.config_id == other.config_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.config_id) + hash(self.config_id)


class Picture(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "tool_picture"
    picture_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    filename = db.Column(db.String(), nullable=False)  # 图片名称
    md5code = db.Column(db.String(), unique=True, nullable=False)  # 文件的md5值
    size = db.Column(db.String(), nullable=False)  # 图片大小
    url = db.Column(db.String(), nullable=False)  # 图片地址
    delete_url = db.Column(db.String(), nullable=False)  # 删除的url
    height = db.Column(db.String(), nullable=False)  # 图片高度
    width = db.Column(db.String(), nullable=False)  # 图片宽度
    username = db.Column(db.String(), nullable=False)  # 用户名称
    create_time = db.Column(db.DateTime())  # 上传日期

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<Picture %r>' % self.picture_id

    def __eq__(self, other):
        if isinstance(other, Picture):
            return self.picture_id == other.picture_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.picture_id) + hash(self.picture_id)


class ToolLocalStorage(Base):
    __tablename__ = "tool_local_storage"
    storage_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    real_name = db.Column(db.String(), nullable=False)  # 文件真实的名称
    name = db.Column(db.String(), nullable=False)  # 文件名
    suffix = db.Column(db.String(), nullable=False)  # 后缀
    path = db.Column(db.String(), nullable=False)  # 路径
    type = db.Column(db.String(), nullable=False)  # 类型
    size = db.Column(db.String(), nullable=False)  # 大小

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<ToolLocalStorage %r>' % self.storage_id

    def __eq__(self, other):
        if isinstance(other, ToolLocalStorage):
            return self.storage_id == other.storage_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.storage_id) + hash(self.storage_id)


class ToolQiniuContent(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "tool_qiniu_content"
    content_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)
    bucket = db.Column(db.String())  # Bucket 识别符
    name = db.Column(db.String(), unique=True)  # 文件名称
    size = db.Column(db.String())  # 文件大小
    type = db.Column(db.String())  # 文件类型：私有或公开
    url = db.Column(db.String())  # 文件url
    suffix = db.Column(db.String())  # 文件后缀
    update_time = db.Column(db.DateTime())  # 上传或同步的时间

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<ToolQiniuContent %r>' % self.content_id

    def __eq__(self, other):
        if isinstance(other, ToolQiniuContent):
            return self.content_id == other.content_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.content_id) + hash(self.content_id)


class ToolQiniuConfig(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    __tablename__ = "tool_qiniu_config"
    config_id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True, unique=True, index=True)  # ID
    access_key = db.Column(db.String())  # accessKey
    bucket = db.Column(db.String())  # Bucket 识别符
    host = db.Column(db.String(), nullable=False)  # 外链域名
    secret_key = db.Column(db.String())  # secretKey
    type = db.Column(db.String())  # 空间类型
    zone = db.Column(db.String())  # 机房

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not k.startswith("_") and hasattr(self, k):
                setattr(self, k, v)

    def __repr__(self):
        return '<ToolQiniuConfig %r>' % self.config_id

    def __eq__(self, other):
        if isinstance(other, ToolQiniuConfig):
            return self.config_id == other.config_id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.config_id) + hash(self.config_id)
