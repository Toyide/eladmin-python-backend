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

# @Time    : 2022/8/17 19:58
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : schema.py
# @Project : eladmin_py_backend
import datetime

from marshmallow import Schema, fields, post_load

from src.models import ToolEmailConfig, QuartzJob, QuartzLog, Menu, Job, Role, Dept, User, Dict, DictDetail, \
    MntDatabase, ToolAlipayConfig, CodeColumnConfig, CodeGenConfig, MntApp, Picture, ToolLocalStorage, ToolQiniuContent, \
    ToolQiniuConfig, MntServer

truthy = {
    "t",
    "T",
    "true",
    "True",
    "TRUE",
    "on",
    "On",
    "ON",
    "y",
    "Y",
    "yes",
    "Yes",
    "YES",
    "1",
    1,
    True,
    b'\x01',
}
falsy = {
    "f",
    "F",
    "false",
    "False",
    "FALSE",
    "off",
    "Off",
    "OFF",
    "n",
    "N",
    "no",
    "No",
    "NO",
    "0",
    0,
    0.0,
    False,
    b'\x00',
    None,
}


class QuartzJobSchema(Schema):
    id = fields.Int(attribute="job_id", load_from='id', allow_none=True)
    jobName = fields.Str(attribute="job_name", load_from='jobName', required=True)
    beanName = fields.Str(attribute="bean_name", load_from='beanName', required=True)
    cronExpression = fields.Str(attribute="cron_expression", load_from='cronExpression', required=True)
    methodName = fields.Str(attribute="method_name", load_from='methodName', required=True)
    isPause = fields.Bool(attribute="is_pause", load_from='isPause', truthy=truthy, falsy=falsy)
    params = fields.Str(required=False, allow_none=True)
    personInCharge = fields.Str(attribute="person_in_charge", load_from='personInCharge', required=True)
    email = fields.Str(required=False, allow_none=True)
    subTask = fields.Str(attribute="sub_task", load_from='subTask', required=False,
                         allow_none=True)
    pauseAfterFailure = fields.Bool(truthy=truthy, falsy=falsy, attribute="pause_after_failure",
                                    load_from='pauseAfterFailure')
    description = fields.Str(required=True)
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = QuartzJob

    @post_load
    def make_quartz_job(self, data: dict, **kwargs):
        return QuartzJob(**data)


class QuartzLogSchema(Schema):
    id = fields.Int(attribute="log_id", load_from='id', allow_none=True)
    jobName = fields.Str(attribute="job_name", load_from='jobName', required=False, allow_none=True)
    beanName = fields.Str(attribute="bean_name", load_from='beanName', required=False, allow_none=True)
    cronExpression = fields.Str(attribute="cron_expression", load_from='cronExpression', required=False,
                                allow_none=True)
    methodName = fields.Str(attribute="method_name", load_from='methodName', required=False, allow_none=True)
    isSuccess = fields.Bool(attribute="is_success", load_from='isSuccess', truthy=truthy, falsy=falsy)
    params = fields.Str()
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    exceptionDetail = fields.Str(attribute="exception_detail", load_from='exceptionDetail', required=False,
                                 allow_none=True)
    log_time = fields.Int(attribute="time", load_from='time', required=False, allow_none=True)

    class Meta:
        model = QuartzLog

    @post_load
    def make_quartz_log(self, data: dict, **kwargs):
        return QuartzLog(**data)


class MenuSchema(Schema):
    id = fields.Int(attribute="menu_id", load_from='id', allow_none=True)
    pid = fields.Int(required=False, allow_none=True)
    type = fields.Int(required=False, allow_none=True)
    title = fields.Str(required=True)
    name = fields.Str(required=False, allow_none=True)
    component = fields.Str(required=False, allow_none=True)
    menuSort = fields.Int(attribute="menu_sort", required=False, allow_none=True)
    subCount = fields.Int(attribute="sub_count", load_from='subCount', required=False, allow_none=True)
    icon = fields.Str(required=False, allow_none=True)
    path = fields.Str(required=True)
    iframe = fields.Bool(truthy=truthy, falsy=falsy, attribute="i_frame", load_from='iframe', required=False,
                         allow_none=True)
    cache = fields.Bool(truthy=truthy, falsy=falsy, required=False, allow_none=True)
    hidden = fields.Bool(truthy=truthy, falsy=falsy, required=False, allow_none=True)
    permission = fields.Str(required=False, allow_none=True)
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = Menu

    @post_load
    def make_menu(self, data: dict, **kwargs):
        return Menu(**data)


class JobSchema(Schema):
    id = fields.Int(attribute="job_id", load_from='id', allow_none=True)
    name = fields.Str()
    enabled = fields.Bool(truthy=truthy, falsy=falsy)
    jobSort = fields.Int(attribute="job_sort", load_from='jobSort')
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = Job

    @post_load
    def make_job(self, data: dict, **kwargs):
        return Job(**data)


class DeptSchema(Schema):
    id = fields.Int(attribute="dept_id", load_from='id', allow_none=True)
    name = fields.Str(required=False)
    pid = fields.Int(allow_none=True)
    enabled = fields.Bool(truthy=truthy, falsy=falsy, required=False)
    subCount = fields.Int(attribute="sub_count", load_from='subCount')
    deptSort = fields.Int(attribute="dept_sort", load_from='deptSort')
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = Dept

    @post_load
    def make_dept(self, data: dict, **kwargs):
        return Dept(**data)


class RoleSchema(Schema):
    id = fields.Int(attribute="role_id", load_from='id', allow_none=True)
    name = fields.Str()
    level = fields.Int()
    description = fields.Str(required=False, allow_none=True)
    dataScope = fields.Str(attribute="data_scope", load_from='dataScope')
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)
    menus = fields.Nested(MenuSchema, many=True, unknown="exclude")
    depts = fields.Nested(DeptSchema, many=True, unknown="exclude")

    class Meta:
        model = Role

    @post_load
    def make_role(self, data: dict, **kwargs):
        return Role(**data)


class UserSchema(Schema):
    # load(dict) -> obj
    id = fields.Int(attribute="user_id", load_from='id', allow_none=True)
    username = fields.Str(load_from='username')
    nickName = fields.Str(attribute="nick_name", load_from='nickName')
    password = fields.Str()
    email = fields.Str()
    phone = fields.Str()
    gender = fields.Str(required=False, allow_none=True)
    avatarName = fields.Str(attribute="avatar_name", load_from='avatarName', required=False, allow_none=True)
    avatarPath = fields.Str(attribute="avatar_path", load_from='avatarPath', required=False, allow_none=True)
    enabled = fields.Bool(truthy=truthy, falsy=falsy, required=False)
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)
    pwdResetTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="pwd_reset_time",
                                   load_from='pwdResetTime', required=False, allow_none=True)
    is_admin = fields.Bool(truthy=truthy, falsy=falsy, load_from='isAdmin', required=False)
    deptId = fields.Int(attribute="dept_id", load_from='deptId', required=False)
    roles = fields.Nested(RoleSchema, many=True)
    jobs = fields.Nested(JobSchema, many=True)
    dept = fields.Nested(DeptSchema)

    class Meta:
        model = User

    @post_load
    def make_user(self, data: dict, **kwargs):
        return User(**data)


class JwtUser:
    user = {}
    dataScopes = []
    roles = []

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {"user": self.user, "dataScopes": self.dataScopes, "roles": self.roles}


class OnlineUser:
    id = ""
    username = ""
    nick_name = ""
    dept = ""
    browser = ""  # request.user_agent
    ip = ""  # request.remote_addr
    address = ""
    key = ""  # token
    loginTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    roles = []

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "nickName": self.nick_name, "dept": self.dept,
                "browser": self.browser, "ip": self.ip, "address": self.address, "key": self.key,
                "loginTime": self.loginTime, "roles": self.roles}


class DictSchema(Schema):
    # load(dict) -> obj
    id = fields.Int(attribute="dict_id", load_from='id', allow_none=True)
    name = fields.Str(load_from='name')
    description = fields.Str(attribute="description", load_from='description')
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)

    # createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
    #                              required=False, allow_none=True)
    # updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
    #                              required=False, allow_none=True)

    class Meta:
        model = Dict

    @post_load
    def make_dict(self, data: dict, **kwargs):
        return Dict(**data)


class DictDetailSchema(Schema):
    # load(dict) -> obj
    id = fields.Int(attribute="detail_id", load_from='id', allow_none=True)
    name = fields.Str()
    label = fields.Str()
    value = fields.Str()
    dictSort = fields.Int(attribute="dict_sort", load_from='dictSort')
    dictId = fields.Int(attribute="dict_id", load_from='dict_id', allow_none=True)
    dict_ = fields.Nested(DictSchema, attribute="dict", unknown="exclude", only=["id"])
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = DictDetail

    @post_load
    def make_dictdetail(self, data: dict, **kwargs):
        return DictDetail(**data)


class DatabaseSchema(Schema):
    id = fields.Str(attribute="db_id", load_from='id', allow_none=True)
    name = fields.Str()
    jdbcUrl = fields.Str(attribute="jdbc_url", load_from='jdbcUrl')
    pwd = fields.Str(attribute="pwd", load_from='pwd')
    userName = fields.Str(attribute="user_name", load_from='userName')
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updatedBy = fields.Str(attribute="update_by", load_from='updatedBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = MntDatabase

    @post_load
    def make_database(self, data: dict, **kwargs):
        return MntDatabase(**data)


class ToolAlipayConfigSchema(Schema):
    id = fields.Int(attribute="config_id", load_from='id', allow_none=True)
    appId = fields.Str(attribute="app_id", load_from='appId', required=False, allow_none=True)
    charset = fields.Str(attribute="charset", load_from='charset', required=False, allow_none=True)
    format = fields.Str(attribute="format", load_from='format', required=False, allow_none=True)
    gatewayUrl = fields.Str(attribute="gateway_url", load_from='gatewayUrl', required=False, allow_none=True)
    notifyUrl = fields.Str(attribute="notify_url", load_from='notifyUrl', required=False, allow_none=True)
    privateKey = fields.Str(attribute="private_key", load_from='privateKey', required=False, allow_none=True)
    publicKey = fields.Str(attribute="public_key", load_from='publicKey', required=False, allow_none=True)
    returnUrl = fields.Str(attribute="return_url", load_from='returnUrl', required=False, allow_none=True)
    signType = fields.Str(attribute="sign_type", load_from='signType', required=False, allow_none=True)
    sysServiceProviderId = fields.Str(attribute="sys_service_provider_id", load_from='sysServiceProviderId',
                                      required=False, allow_none=True)

    class Meta:
        model = ToolAlipayConfig

    @post_load
    def make_tool_alipay_config(self, data: dict, **kwargs):
        return ToolAlipayConfig(**data)


class CodeColumnConfigSchema(Schema):
    id = fields.Int(attribute="column_id", load_from='id', allow_none=True)
    tableName = fields.Str(attribute="table_name", load_from='tableName', required=False, allow_none=True)
    columnName = fields.Str(attribute="column_name", load_from='columnName', required=False, allow_none=True)
    columnType = fields.Str(attribute="column_type", load_from='columnType', required=False, allow_none=True)
    dictName = fields.Str(attribute="dict_name", load_from='dictName', required=False, allow_none=True)
    extra = fields.Str(attribute="extra", load_from='extra', required=False, allow_none=True)
    formShow = fields.Bool(attribute="form_show", load_from='formShow', truthy=truthy, falsy=falsy, required=False)
    formType = fields.Str(attribute="form_type", load_from='formType', required=False, allow_none=True)
    keyType = fields.Str(attribute="key_type", load_from='keyType', required=False, allow_none=True)
    listShow = fields.Bool(attribute="list_show", load_from='listShow', truthy=truthy, falsy=falsy, required=False)
    notNull = fields.Bool(attribute="not_null", load_from='notNull', truthy=truthy, falsy=falsy, required=False)
    queryType = fields.Str(attribute="query_type", load_from='queryType', required=False, allow_none=True)
    remark = fields.Str(attribute="remark", load_from='remark', required=False, allow_none=True)
    dateAnnotation = fields.Str(attribute="date_annotation", load_from='dateAnnotation', required=False,
                                allow_none=True)

    class Meta:
        model = CodeColumnConfig

    @post_load
    def make_code_column_config(self, data: dict, **kwargs):
        return CodeColumnConfig(**data)


class GenConfigSchema(Schema):
    id = fields.Int(attribute="config_id", load_from='id', allow_none=True)
    tableName = fields.Str(attribute="table_name", load_from='tableName', required=True, allow_none=False)
    author = fields.Str(attribute="author", load_from='author', required=True, allow_none=False)
    cover = fields.Bool(attribute="cover", load_from='cover', truthy=truthy, falsy=falsy, required=True,
                        allow_none=False)
    moduleName = fields.Str(attribute="module_name", load_from='moduleName', required=True, allow_none=False)
    pack = fields.Str(attribute="pack", load_from='pack', required=True, allow_none=False)
    path = fields.Str(attribute="path", load_from='path', required=True, allow_none=False)
    apiPath = fields.Str(attribute="api_path", load_from='apiPath', required=False, allow_none=True)
    prefix = fields.Str(attribute="prefix", load_from='prefix', required=False, allow_none=True)
    apiAlias = fields.Str(attribute="api_alias", load_from='apiAlias', required=True, allow_none=False)

    class Meta:
        model = CodeGenConfig

    @post_load
    def make_code_gen_config(self, data: dict, **kwargs):
        return CodeGenConfig(**data)


class ToolEmailConfigSchema(Schema):
    id = fields.Int(attribute="config_id", load_from='id', allow_none=True)
    fromUser = fields.Str(attribute="from_user", load_from='fromUser', required=True, allow_none=False)
    host = fields.Str(attribute="host", load_from='host', required=True, allow_none=False)
    password = fields.Str(attribute="pass", load_from='pass', dump_to='pass', required=False, allow_none=True)
    port = fields.Str(attribute="port", load_from='port', required=True, allow_none=False)
    user = fields.Str(attribute="user", load_from='user', required=True, allow_none=False)

    class Meta:
        model = ToolEmailConfig

    @post_load
    def make_tool_email_config(self, data: dict, **kwargs):
        return ToolEmailConfig(**data)


class AppSchema(Schema):
    id = fields.Int(attribute="app_id", load_from='id', allow_none=True)
    port = fields.Int(attribute="port", load_from='port', required=True, allow_none=False)
    name = fields.Str(attribute="name", load_from='name', required=True, allow_none=False)
    uploadPath = fields.Str(attribute="upload_path", load_from='uploadPath', required=True, allow_none=False)
    deployPath = fields.Str(attribute="deploy_path", load_from='deployPath', required=True, allow_none=False)
    backupPath = fields.Str(attribute="backup_path", load_from='backupPath', required=True, allow_none=False)
    startScript = fields.Str(attribute="start_script", load_from='startScript', required=True, allow_none=False)
    deployScript = fields.Str(attribute="deploy_script", load_from='deployScript', required=True, allow_none=False)
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updateBy = fields.Str(attribute="update_by", load_from='updateBy', required=False, allow_none=True)

    class Meta:
        model = MntApp

    @post_load
    def make_app(self, data: dict, **kwargs):
        return MntApp(**data)


class PictureSchema(Schema):
    id = fields.Int(attribute="picture_id", load_from='id', allow_none=True)
    filename = fields.Str(attribute="filename", load_from='filename', required=False, allow_none=True)
    md5code = fields.Str(attribute="md5code", load_from='md5code', required=False, allow_none=True)
    size = fields.Int(attribute="size", load_from='size', required=False, allow_none=True)
    url = fields.Str(attribute="url", load_from='url', required=False, allow_none=True)
    delete = fields.Str(attribute="delete_url", load_from='delete', required=False, allow_none=True)
    height = fields.Int(attribute="height", load_from='height', required=False, allow_none=True)
    width = fields.Int(attribute="width", load_from='width', required=False, allow_none=True)
    username = fields.Str(attribute="username", load_from='username', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)

    class Meta:
        model = Picture

    @post_load
    def make_tool_picture(self, data: dict, **kwargs):
        return Picture(**data)


class ToolLocalStorageSchema(Schema):
    id = fields.Int(attribute="storage_id", load_from='id', allow_none=True)
    realName = fields.Str(attribute="real_name", load_from='realName', required=True, allow_none=False)
    name = fields.Str(attribute="name", load_from='name', required=True, allow_none=False)
    suffix = fields.Str(attribute="suffix", load_from='suffix', required=True, allow_none=False)
    path = fields.Str(attribute="path", load_from='path', required=True, allow_none=False)
    type = fields.Str(attribute="type", load_from='type', required=True, allow_none=False)
    size = fields.Str(attribute="size", load_from='size', required=True, allow_none=False)
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updateBy = fields.Str(attribute="update_by", load_from='updateBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = ToolLocalStorage

    @post_load
    def make_tool_local_storage(self, data: dict, **kwargs):
        return ToolLocalStorage(**data)


class ToolQiniuContentSchema(Schema):
    id = fields.Int(attribute="content_id", load_from='id', allow_none=True)
    bucket = fields.Str(attribute="bucket", load_from='bucket', required=False, allow_none=True)
    name = fields.Str(attribute="name", load_from='name', required=False, allow_none=True)
    size = fields.Str(attribute="size", load_from='size', required=False, allow_none=True)
    type = fields.Str(attribute="type", load_from='type', required=False, allow_none=True)
    url = fields.Str(attribute="url", load_from='url', required=False, allow_none=True)
    suffix = fields.Str(attribute="suffix", load_from='suffix', required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = ToolQiniuContent

    @post_load
    def make_tool_qiniu_content(self, data: dict, **kwargs):
        return ToolQiniuContent(**data)


class ToolQiniuConfigSchema(Schema):
    id = fields.Int(attribute="config_id", load_from='id', allow_none=True)
    accessKey = fields.Str(attribute="access_key", load_from='accessKey', required=False, allow_none=True)
    bucket = fields.Str(attribute="bucket", load_from='bucket', required=False, allow_none=True)
    host = fields.Str(attribute="host", load_from='host', required=True, allow_none=False)
    secretKey = fields.Str(attribute="secret_key", load_from='secretKey', required=False, allow_none=True)
    type = fields.Str(attribute="type", load_from='type', required=False, allow_none=True)
    zone = fields.Str(attribute="zone", load_from='zone', required=False, allow_none=True)

    class Meta:
        model = ToolQiniuConfig

    @post_load
    def make_tool_qiniu_config(self, data: dict, **kwargs):
        return ToolQiniuConfig(**data)


class MntServerSchema(Schema):
    id = fields.Int(attribute="server_id", load_from='id', allow_none=True)
    account = fields.Str(attribute="account", load_from='account', required=True)
    ip = fields.Str(attribute="ip", load_from='ip', required=True)
    name = fields.Str(attribute="name", load_from='name', required=True)
    password = fields.Str(attribute="password", load_from='password', required=True)
    port = fields.Int(attribute="port", load_from='port', required=True)
    createBy = fields.Str(attribute="create_by", load_from='createBy', required=False, allow_none=True)
    updateBy = fields.Str(attribute="update_by", load_from='updateBy', required=False, allow_none=True)
    createTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="create_time", load_from='createTime',
                                 required=False, allow_none=True)
    updateTime = fields.DateTime(format="%Y-%m-%d %H:%M:%S", attribute="update_time", load_from='updateTime',
                                 required=False, allow_none=True)

    class Meta:
        model = MntServer

    @post_load
    def make_mnt_server(self, data: dict, **kwargs):
        return MntServer(**data)
