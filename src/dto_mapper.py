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

# @Time    : 2022/6/13 21:47
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : dto_mapper.py
# @Project : eladmin_py_backend
import datetime

from flask_restful import fields


class BItem(fields.Raw):
    def format(self, value):
        if type(value) == bool:
            return value
        else:
            return value[0] == 1


class HasChildrenItem(fields.Raw):
    def format(self, value):
        return True if value > 0 else False


class PidItem(fields.Raw):
    def format(self, value):
        return None if value is None else value


class LeafItem(fields.Raw):
    def format(self, value):
        return True if value <= 0 else False


class DateTimeItem(fields.Raw):
    def format(self, value):
        if value:
            return datetime.datetime.strftime(value, '%Y-%m-%d %H:%M:%S')
        return value


class ServerItem(fields.Raw):
    def format(self, value):
        if value:
            # deploys是懒加载，需要执行查询以获取server.name
            return ",".join([server.name for server in value.all()])
        return value


user_roles_fields = {
    'id': fields.Integer(attribute="role_id"),
    'name': fields.String,
    'level': fields.Integer,
    'dataScope': fields.String(attribute="data_scope")
}

user_jobs_fields = {
    'id': fields.Integer(attribute="job_id"),
    'name': fields.String,
}

user_dept_fields = {
    'id': fields.Integer(attribute="dept_id"),
    'name': fields.String,
}

user_edit_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="user_id"),
    'roles': fields.List(fields.Nested(user_roles_fields)),
    'jobs': fields.List(fields.Nested(user_jobs_fields)),
    'dept': fields.Nested(user_dept_fields),
    'deptId': fields.Integer(attribute="dept_id"),
    'is_admin': BItem(attribute="is_admin"),
    'username': fields.String,
    'nickName': fields.String(attribute="nick_name"),
    'email': fields.String,
    'phone': fields.String,
    'gender': fields.String,
    'avatarName': fields.String(attribute="avatar_name"),
    'avatarPath': fields.String(attribute="avatar_path"),
    'password': fields.String(attribute="password"),
    'enabled': fields.Boolean,
    'pwdResetTime': DateTimeItem(attribute="pwd_reset_time")
}

user_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="user_id"),
    'roles': fields.List(fields.Nested(user_roles_fields)),
    'jobs': fields.List(fields.Nested(user_jobs_fields)),
    'dept': fields.Nested(user_dept_fields, attribute='user_dept'),
    'deptId': fields.Integer(attribute="dept_id"),
    'is_admin': BItem(attribute="is_admin"),
    'username': fields.String,
    'nickName': fields.String(attribute="nick_name"),
    'email': fields.String,
    'phone': fields.String,
    'gender': fields.String,
    'avatarName': fields.String(attribute="avatar_name"),
    'avatarPath': fields.String(attribute="avatar_path"),
    'enabled': fields.Boolean,
    'pwdResetTime': DateTimeItem(attribute="pwd_reset_time")
}

dept_child_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="dept_id"),
    'name': fields.String,
    'enabled': BItem(attribute="enabled"),
    'deptSort': fields.Integer(attribute="dept_sort"),
    'pid': PidItem(attribute="pid"),
    'subCount': fields.Integer(attribute="sub_count"),
    'hasChildren': HasChildrenItem(attribute="sub_count"),
    'leaf': LeafItem(attribute="sub_count"),
    'label': fields.String(attribute="name")
}

dept_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="dept_id"),
    'name': fields.String,
    'enabled': BItem(attribute="enabled"),
    'deptSort': fields.Integer(attribute="dept_sort"),
    'pid': PidItem(attribute="pid"),
    'subCount': fields.Integer(attribute="sub_count"),
    'hasChildren': HasChildrenItem(attribute="sub_count"),
    'leaf': LeafItem(attribute="sub_count"),
    'label': fields.String(attribute="name"),
    'children': fields.List(fields.Nested(dept_child_fields), attribute="children")
}

dept_page_fields = {
    'content': fields.List(fields.Nested(dept_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

dict_detail_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="detail_id"),
    'label': fields.String,
    'value': fields.String,
    'dictSort': fields.Integer(attribute="dict_sort")
}

dictdetail_page_fields = {
    'content': fields.List(fields.Nested(dict_detail_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

dict_fields = {
    'id': fields.Integer(attribute="dict_id"),
    'name': fields.String,
    'description': fields.String,
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time")
}

dict_page_fields = {
    'content': fields.List(fields.Nested(dict_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

job_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="job_id"),
    'jobSort': fields.Integer(attribute="job_sort"),
    'name': fields.String,
    'enabled': BItem(attribute="enabled")
}

job_page_fields = {
    'content': fields.List(fields.Nested(job_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

menu_child_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="menu_id"),
    'type': fields.Integer,
    'permission': fields.String,
    'title': fields.String,
    'menuSort': fields.Integer(attribute="menu_sort"),
    'path': fields.String,
    'component': fields.String,
    'pid': PidItem(attribute="pid"),
    'subCount': fields.Integer(attribute="sub_count"),
    'cache': BItem(attribute="cache"),
    'hidden': BItem(attribute="hidden"),
    'componentName': fields.String(attribute="name"),
    'icon': fields.String,
    'hasChildren': HasChildrenItem(attribute="sub_count"),
    'leaf': LeafItem(attribute="sub_count"),
    'label': fields.String(attribute="title"),
    'iframe': BItem(attribute="i_frame"),
}

menu_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="menu_id"),
    'type': fields.Integer,
    'permission': fields.String,
    'title': fields.String,
    'menuSort': fields.Integer(attribute="menu_sort"),
    'path': fields.String,
    'component': fields.String,
    'pid': PidItem(attribute="pid"),
    'subCount': fields.Integer(attribute="sub_count"),
    'cache': BItem(attribute="cache"),
    'hidden': BItem(attribute="hidden"),
    'componentName': fields.String(attribute="name"),
    'icon': fields.String,
    'hasChildren': HasChildrenItem(attribute="sub_count"),
    'leaf': LeafItem(attribute="sub_count"),
    'label': fields.String(attribute="title"),
    'iframe': BItem(attribute="i_frame"),
    'children': fields.List(fields.Nested(menu_child_fields), attribute="children")
}

menu_page_fields = {
    'content': fields.List(fields.Nested(menu_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

role_edit_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="role_id"),
    'menus': fields.List(fields.Nested(menu_fields)),
    'depts': fields.List(fields.Nested(dept_fields)),
    'name': fields.String,
    'dataScope': fields.String(attribute="data_scope"),
    'level': fields.Integer,
    'description': fields.String
}

role_fields = {
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'id': fields.Integer(attribute="role_id"),
    'menus': fields.List(fields.Nested(menu_fields)),
    'depts': fields.List(fields.Nested(dept_fields)),
    'name': fields.String,
    'dataScope': fields.String(attribute="data_scope"),
    'level': fields.Integer,
    'description': fields.String
}

role_page_fields = {
    'content': fields.List(fields.Nested(role_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

user_page_fields = {
    'content': fields.List(fields.Nested(user_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

quartz_job_fields = {
    'id': fields.Integer(attribute="job_id"),
    'jobName': fields.String(attribute="job_name"),
    'beanName': fields.String(attribute="bean_name"),
    'cronExpression': fields.String(attribute="cron_expression"),
    'methodName': fields.String(attribute="method_name"),
    'isPause': BItem(attribute="is_pause"),
    'params': fields.String,
    'personInCharge': fields.String(attribute="person_in_charge"),
    'email': fields.String,
    'subTask': fields.String(attribute="sub_task"),
    'pauseAfterFailure': BItem(attribute="pause_after_failure"),
    'description': fields.String,
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time")
}

quartz_job_page_fields = {
    'content': fields.List(fields.Nested(quartz_job_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

quartz_log_fields = {
    'id': fields.Integer(attribute="log_id"),
    'jobName': fields.String(attribute="job_name"),
    'beanName': fields.String(attribute="bean_name"),
    'cronExpression': fields.String(attribute="cron_expression"),
    'methodName': fields.String(attribute="method_name"),
    'params': fields.String,
    'exceptionDetail': fields.String(attribute="exception_detail"),
    'time': fields.Integer(attribute="log_time"),
    'isSuccess': BItem(attribute="is_success"),
    'createTime': DateTimeItem(attribute="create_time")
}

quartz_log_page_fields = {
    'content': fields.List(fields.Nested(quartz_log_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

logs_fields = {
    'id': fields.Integer(attribute="log_id"),
    'username': fields.String(attribute="username"),
    'description': fields.String(attribute="description"),
    'method': fields.String(attribute="method"),
    'params': fields.String(attribute="params"),
    'logType': fields.String(attribute="log_type"),
    'requestIp': fields.String(attribute="request_ip"),
    'address': fields.String(attribute="address"),
    'browser': fields.String(attribute="browser"),
    'time': fields.Integer(attribute="log_time"),
    'exceptionDetail': fields.String(attribute="exception_detail"),
    'exception': fields.String(attribute="exception_detail"),
    'createTime': DateTimeItem(attribute="create_time")
}

logs_page_fields = {
    'content': fields.List(fields.Nested(logs_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

server_deploy_fields = {
    'id': fields.Integer(attribute="server_id"),
    'name': fields.String(attribute="name"),
    'ip': fields.String(attribute="ip"),
    'port': fields.Integer(attribute="port"),
    'account': fields.String(attribute="account"),
    'password': fields.String(attribute="password"),
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time")
}

server_deploy_page_fields = {
    'content': fields.List(fields.Nested(server_deploy_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

app_fields = {
    'id': fields.Integer(attribute="app_id"),
    'name': fields.String(attribute="name"),
    'uploadPath': fields.String(attribute="upload_path"),
    'deployPath': fields.String(attribute="deploy_path"),
    'backupPath': fields.String(attribute="backup_path"),
    'port': fields.Integer(attribute="port"),
    'startScript': fields.String(attribute="start_script"),
    'deployScript': fields.String(attribute="deploy_script"),
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time")
}

app_page_fields = {
    'content': fields.List(fields.Nested(app_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

deploy_fields = {
    'id': fields.Integer(attribute="deploy_id"),
    'appId': fields.String(attribute="app_id"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
    'deploys': fields.List(fields.Nested(server_deploy_fields)),
    'servers': ServerItem(attribute="deploys"),
    'app': fields.Nested(app_fields)
}

deploy_page_fields = {
    'content': fields.List(fields.Nested(deploy_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

deployhistory_fields = {
    'id': fields.String(attribute="history_id"),
    'appName': fields.String(attribute="app_name"),
    'ip': fields.String(attribute="ip"),
    'deployDate': DateTimeItem(attribute="deploy_date"),
    'deployUser': fields.String(attribute="deploy_user"),
    'deployId': fields.Integer(attribute="deploy_id"),
}

deployhistory_page_fields = {
    'content': fields.List(fields.Nested(deployhistory_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

database_fields = {
    'id': fields.String(attribute="db_id"),
    'name': fields.String(attribute="name"),
    'jdbcUrl': fields.String(attribute="jdbc_url"),
    'pwd': fields.String(attribute="pwd"),
    'userName': fields.String(attribute="user_name"),
    'createBy': fields.String(attribute="create_by"),
    'updatedBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time")
}

database_page_fields = {
    'content': fields.List(fields.Nested(database_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

alipay_fields = {
    'id': fields.Integer(attribute="config_id"),
    'appId': fields.String(attribute="app_id"),
    'charset': fields.String(attribute="charset"),
    'format': fields.String(attribute="format"),
    'gatewayUrl': fields.String(attribute="gateway_url"),
    'notifyUrl': fields.String(attribute="notify_url"),
    'privateKey': fields.String(attribute="private_key"),
    'publicKey': fields.String(attribute="public_key"),
    'returnUrl': fields.String(attribute="return_url"),
    'signType': fields.String(attribute="sign_type"),
    'sysServiceProviderId': fields.String(attribute="sys_service_provider_id"),
}

alipay_page_fields = {
    'content': fields.List(fields.Nested(alipay_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

gen_config_fields = {
    'id': fields.Integer(attribute="config_id"),
    'tableName': fields.String(attribute="table_name"),
    'author': fields.String(attribute="author"),
    'cover': BItem(attribute="cover"),
    'moduleName': fields.String(attribute="module_name"),
    'pack': fields.String(attribute="pack"),
    'path': fields.String(attribute="path"),
    'apiPath': fields.String(attribute="api_path"),
    'prefix': fields.String(attribute="prefix"),
    'apiAlias': fields.String(attribute="api_alias")
}

column_fields = {
    'id': fields.Integer(attribute="column_id"),
    'tableName': fields.String(attribute="table_name"),
    'columnName': fields.String(attribute="column_name"),
    'columnType': fields.String(attribute="column_type"),
    'dictName': fields.String(attribute="dict_name"),
    'extra': fields.String(attribute="extra"),
    'formShow': BItem(attribute="form_show"),
    'formType': fields.String(attribute="form_type"),
    'keyType': fields.String(attribute="key_type"),
    'listShow': BItem(attribute="list_show"),
    'notNull': BItem(attribute="not_null"),
    'queryType': fields.String(attribute="query_type"),
    'remark': fields.String(attribute="remark"),
    'dateAnnotation': fields.String(attribute="date_annotation")
}

tool_email_config_fields = {
    'id': fields.Integer(attribute="config_id"),
    'fromUser': fields.String(attribute="from_user"),
    'host': fields.String(attribute="host"),
    'pass': fields.String(attribute="password"),
    'port': fields.String(attribute="port"),
    'user': fields.String(attribute="user"),
}

tool_picture_fields = {
    'id': fields.Integer(attribute="picture_id"),
    'filename': fields.String(attribute="filename"),
    'md5code': fields.String(attribute="md5code"),
    'size': fields.String(attribute="size"),
    'url': fields.String(attribute="url"),
    'deleteUrl': fields.String(attribute="delete_url"),
    'height': fields.String(attribute="height"),
    'width': fields.String(attribute="width"),
    'username': fields.String(attribute="username"),
    'createTime': DateTimeItem(attribute="create_time"),
}

tool_picture_page_fields = {
    'content': fields.List(fields.Nested(tool_picture_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

tool_local_storage_fields = {
    'id': fields.Integer(attribute="storage_id"),
    'realName': fields.String(attribute="real_name"),
    'name': fields.String(attribute="name"),
    'suffix': fields.String(attribute="suffix"),
    'path': fields.String(attribute="path"),
    'type': fields.String(attribute="type"),
    'size': fields.String(attribute="size"),
    'operate': fields.String(attribute="create_by"),
    'createBy': fields.String(attribute="create_by"),
    'updateBy': fields.String(attribute="update_by"),
    'createTime': DateTimeItem(attribute="create_time"),
    'updateTime': DateTimeItem(attribute="update_time"),
}

tool_local_storage_page_fields = {
    'content': fields.List(fields.Nested(tool_local_storage_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

tool_qiniu_content_fields = {
    'contentId': fields.Integer(attribute="content_id"),
    'bucket': fields.String(attribute="bucket"),
    'name': fields.String(attribute="name"),
    'size': fields.String(attribute="size"),
    'type': fields.String(attribute="type"),
    'url': fields.String(attribute="url"),
    'suffix': fields.String(attribute="suffix"),
    'updateTime': DateTimeItem(attribute="update_time"),
}

tool_qiniu_content_page_fields = {
    'content': fields.List(fields.Nested(tool_qiniu_content_fields), attribute="items"),
    'totalElements': fields.Integer(attribute="total")
}

tool_qiniu_config_fields = {
    'id': fields.Integer(attribute="config_id"),
    'accessKey': fields.String(attribute="access_key"),
    'bucket': fields.String(attribute="bucket"),
    'host': fields.String(attribute="host"),
    'secretKey': fields.String(attribute="secret_key"),
    'type': fields.String(attribute="type"),
    'zone': fields.String(attribute="zone"),
}
