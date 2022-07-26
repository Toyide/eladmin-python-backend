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

# @Time    : 2022/8/9 11:28
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : sys_tools_service.py
# @Project : eladmin_py_backend
import datetime
import os
import smtplib
import traceback
from collections import OrderedDict
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

import requests
from sqlalchemy import or_

from src import db
from src.config import api_utils
from src.dto_mapper import tool_picture_fields, tool_local_storage_fields, tool_qiniu_content_fields
from src.extensions import AppException
from src.models import CodeGenConfig, CodeColumnConfig, ToolAlipayConfig, ToolEmailConfig, Picture, ToolLocalStorage, \
    ToolQiniuContent, ToolQiniuConfig
from src.tools import trim_and_lower, format_date, des_encrypt, des_decrypt, download_excel


class GenConfigService:
    @staticmethod
    def find(table_name: str) -> CodeGenConfig:
        conf = db.session.query(CodeGenConfig).filter(CodeGenConfig.table_name == table_name).one_or_none()
        if conf is None:
            return CodeGenConfig(table_name=table_name)
        return conf

    @staticmethod
    def update(curr_gen: CodeGenConfig):
        rs = None
        if curr_gen.config_id:
            old_gen = db.session.query(CodeGenConfig).filter(
                CodeGenConfig.config_id == curr_gen.config_id).one_or_none()
            if old_gen is None:
                new_gen = CodeGenConfig()
                GenConfigService.convert(new_gen, curr_gen)
                db.session.add(new_gen)
                rs = new_gen
            else:
                GenConfigService.convert(old_gen, curr_gen)
                rs = old_gen
        else:
            new_gen = CodeGenConfig()
            GenConfigService.convert(new_gen, curr_gen)
            db.session.add(new_gen)
            rs = new_gen
        db.session.commit()
        return rs

    @staticmethod
    def convert(old_obj: CodeGenConfig, new_obj: CodeGenConfig):
        old_obj.table_name = new_obj.table_name
        old_obj.author = new_obj.author
        old_obj.cover = new_obj.cover
        old_obj.module_name = new_obj.module_name
        old_obj.pack = new_obj.pack
        old_obj.path = new_obj.path
        old_obj.api_path = new_obj.api_path
        if not new_obj.api_path:
            path = new_obj.path.replace('\\', '/')
            arr = path.split('/')
            rs = []
            for p in arr:
                rs.append(p)
                rs.append(os.sep)
                if p == 'src':
                    rs.append('api')
                    break
            old_obj.api_path = ''.join(rs)
        old_obj.prefix = new_obj.prefix
        old_obj.api_alias = new_obj.api_alias


class GeneratorService:
    @staticmethod
    def get_tables(page=0, size=9999, **kwargs):
        page = int(page)
        size = int(size)
        name = kwargs.get("name", "")
        sql = f'select table_name, create_time, engine, table_collation, table_comment from ' \
            f'information_schema.tables where table_schema = (select database()) ' \
            f'and table_name like "%{name}%" order by create_time desc ' \
            f'limit {page * size}, {(page + 1) * size}'
        sql_result = db.session.execute(sql).fetchall()
        count_sql = f'SELECT COUNT(*) from information_schema.tables where table_schema = (select database())'
        total = db.session.execute(count_sql).scalar()
        rs = []
        for table in sql_result:
            rs.append({"tableName": trim_and_lower(table["table_name"]),
                       "createTime": format_date(table["create_time"]),
                       "engine": trim_and_lower(table["engine"]),
                       "coding": trim_and_lower(table["table_collation"]),
                       "remark": trim_and_lower(table["table_comment"])})
        return {'content': rs, 'totalElements': total}

    @staticmethod
    def get_columns(table_name: str) -> list:
        columns = db.session.query(CodeColumnConfig).order_by(CodeColumnConfig.column_id.asc()).filter(
            CodeColumnConfig.table_name == table_name).all()
        return columns

    @staticmethod
    def get_gen_dict(column_list: list, gen_config: CodeGenConfig) -> dict:
        # 存储模版字段数据
        gen_map = {"apiAlias": gen_config.api_alias, "package": gen_config.pack, "moduleName": gen_config.module_name,
                   "author": gen_config.author, "date": format_date(datetime.datetime.now()),
                   "year": datetime.datetime.now().year, "tableName": gen_config.table_name,
                   "tableNameLower": gen_config.table_name.lower()}
        className = api_utils.toCapitalizeCamelCase(gen_config.table_name)
        changeClassName = api_utils.toCamelCase(gen_config.table_name)
        if gen_config.prefix:
            className = api_utils.toCapitalizeCamelCase(gen_config.table_name[len(gen_config.prefix):])
            changeClassName = api_utils.toCamelCase(gen_config.table_name[len(gen_config.prefix):])
        gen_map["className"] = className  # 保存类名
        gen_map["changeClassName"] = changeClassName  # 保存小写开头的类名
        # 存在 Timestamp 字段
        gen_map["hasTimestamp"] = False
        # 查询类中存在 Timestamp 字段
        gen_map["queryHasTimestamp"] = False
        # 存在 BigDecimal 字段
        gen_map["hasBigDecimal"] = False
        # 查询类中存在 BigDecimal 字段
        gen_map["queryHasBigDecimal"] = False
        # 是否需要创建查询
        gen_map["hasQuery"] = False
        # 自增主键
        gen_map["auto"] = False
        # 存在字典
        gen_map["hasDict"] = False
        # 存在日期注解
        gen_map["hasDateAnnotation"] = False
        # 保存字段信息
        columns = []
        # 保存查询字段的信息
        queryColumns = []
        # 存储字典信息
        dicts = []
        # 存储 between 信息
        betweens = []
        # 存储不为空的字段信息
        isNotNullColumns = []
        for column in column_list:
            listMap = {}
            listMap["remark"] = column.remark
            listMap["columnKey"] = column.key_type
            colType = api_utils.column_type_convert.get(column.column_type)  # 存储主键类型
            changeColumnName = api_utils.toCamelCase(column.column_name)  # 小写开头的字段名
            capitalColumnName = api_utils.toCapitalizeCamelCase(column.column_name)  # 大写开头的字段名
            if column.key_type == 'PRI':
                gen_map["pkColumnType"] = colType  # 存储主键类型
                gen_map["pkColumnName"] = column.column_name  # 存储主键名
                gen_map["pkChangeColName"] = changeColumnName  # 存储小写开头的字段名
                gen_map["pkCapitalColName"] = capitalColumnName  # 存储小写开头的字段名

            if colType == 'DateTime':
                gen_map["hasTimestamp"] = True  # 是否存在 Timestamp 类型的字段
            elif colType == 'Numeric':
                gen_map["hasBigDecimal"] = True  # 是否存在 Numeric 类型的字段
            elif colType == 'auto_increment':
                gen_map["auto"] = True  # 主键是否自增
            if column.dict_name:
                gen_map["hasDict"] = True  # 主键存在字典
                dicts.append(column.dict_name)
            listMap["columnType"] = colType
            listMap["columnName"] = column.column_name
            listMap["istNotNull"] = True if column.not_null[0] == 1 else False
            listMap["columnShow"] = True if column.list_show[0] == 1 else False
            listMap["formShow"] = True if column.form_show[0] == 1 else False
            listMap["formType"] = column.form_type if column.form_type else 'Input'
            listMap["changeColumnName"] = changeColumnName
            listMap["capitalColumnName"] = capitalColumnName
            listMap["dictName"] = column.dict_name
            listMap["dateAnnotation"] = column.date_annotation
            if column.date_annotation:
                gen_map["hasDateAnnotation"] = True
            if column.not_null[0] == 1:
                isNotNullColumns.append(listMap)
            if column.query_type:
                listMap["queryType"] = column.query_type
                gen_map["hasQuery"] = True
                if colType == 'DateTime':
                    gen_map["queryHasTimestamp"] = True  # 查询中存储 Timestamp 类型
                elif colType == 'Numeric':
                    gen_map["queryHasBigDecimal"] = True  # 查询中存储 BigDecimal 类型
                if column.query_type and column.query_type.lower() == 'between':
                    betweens.append(listMap)
                else:
                    queryColumns.append(listMap)
            # 添加到字段列表中
            columns.append(listMap)
        gen_map["columns"] = columns
        gen_map["queryColumns"] = queryColumns
        gen_map["dicts"] = dicts
        gen_map["betweens"] = betweens
        gen_map["isNotNullColumns"] = isNotNullColumns
        return gen_map

    @staticmethod
    def get_templates() -> list:
        path = os.path.abspath('src/templates')
        return [os.path.join(path, template) for template in os.listdir(path) if 'Email' not in template]

    @staticmethod
    def sync_table(columnInfos: list, columnList: list):
        # 第一种情况，数据库类字段改变或者新增字段
        for col in columnList:
            columns = [x for x in columnInfos if x.column_name == col.column_name]
            if columns:
                # 更新
                column = columns[0]
                column.column_type = col.column_type
                column.extra = col.extra
                column.key_type = col.key_type
                if not column.remark:
                    column.remark = col.remark
                db.session.commit()
            else:
                # 新增
                db.session.add(col)
                db.session.commit()
        del_list = []
        table_name = ""
        # 第二种情况，数据库字段删除了
        for col in columnInfos:
            columns = [x for x in columnList if x.column_name == col.column_name]
            if not columns:
                table_name = col.table_name
                del_list.append(col.column_name)
        if table_name and del_list:
            db.query(CodeColumnConfig).filter(
                (CodeColumnConfig.table_name == table_name), (CodeColumnConfig.column_name.in_(del_list))).delete(
                synchronize_session=False)
            db.session.commit()

    @staticmethod
    def query(table_name: str):
        sql = f'select column_name, is_nullable, data_type, column_comment, column_key, extra ' \
            f'from information_schema.columns where table_name = "{table_name}" ' \
            f'and table_schema = (select database()) order by ordinal_position'
        sql_result = db.session.execute(sql).fetchall()
        rs = []
        for table in sql_result:
            rs.append(CodeColumnConfig(**{"table_name": table_name,
                                          "column_name": trim_and_lower(table["column_name"]),
                                          "not_null": True if table["is_nullable"].lower() == 'no' else False,
                                          "column_type": trim_and_lower(table["data_type"]),
                                          "remark": trim_and_lower(table["column_comment"]),
                                          "key_type": trim_and_lower(table["column_key"]).upper(),
                                          "extra": trim_and_lower(table["extra"])}))
        return rs

    @staticmethod
    def sync(tables: list):
        for table_name in tables:
            GeneratorService.sync_table(GeneratorService.get_columns(table_name=table_name),
                                        GeneratorService.query(table_name=table_name))

    @staticmethod
    def save(curr_configs: list):
        column_ids = {}
        for x in curr_configs:
            column_ids[x.column_id] = x
        if column_ids:
            old_configs = CodeColumnConfig.query.filter(CodeColumnConfig.column_id.in_(column_ids.keys())).all()
            for config in old_configs:
                new_column = column_ids.get(config.column_id)
                if new_column:
                    config.column_type = new_column.column_type
                    config.dict_name = new_column.dict_name
                    config.extra = new_column.extra
                    config.form_show = new_column.form_show
                    config.form_type = new_column.form_type
                    config.key_type = new_column.key_type
                    config.list_show = new_column.list_show
                    config.not_null = new_column.not_null
                    config.query_type = new_column.query_type
                    config.remark = new_column.remark
                    config.date_annotation = new_column.date_annotation
            db.session.commit()


class ToolAlipayConfigService:
    @staticmethod
    def find():
        configs = db.session.query(ToolAlipayConfig).all()
        return configs[0] if configs else None

    @staticmethod
    def update(curr_alipay: ToolAlipayConfig):
        if curr_alipay.config_id:
            old_alipay = ToolAlipayConfig.query.filter(
                ToolAlipayConfig.config_id == curr_alipay.config_id).one_or_none()
            if old_alipay is None:
                old_alipay = ToolAlipayConfig()
            else:
                old_alipay.config_id = curr_alipay.config_id
        else:
            old_alipay = ToolAlipayConfig()

        old_alipay.app_id = curr_alipay.app_id
        old_alipay.charset = curr_alipay.charset
        old_alipay.format = curr_alipay.format
        old_alipay.gateway_url = curr_alipay.gateway_url
        old_alipay.notify_url = curr_alipay.notify_url
        old_alipay.private_key = curr_alipay.private_key
        old_alipay.public_key = curr_alipay.public_key
        old_alipay.return_url = curr_alipay.return_url
        old_alipay.sign_type = curr_alipay.sign_type
        old_alipay.sys_service_provider_id = curr_alipay.sys_service_provider_id
        if not curr_alipay.config_id:
            curr_alipay.config_id = 1
            db.session.add(old_alipay)
        db.session.commit()


class ToolEmailConfigService:
    @staticmethod
    def find() -> ToolEmailConfig:
        configs = db.session.query(ToolEmailConfig).all()
        config = configs[0] if configs else None
        if config and config.password:
            config.password = des_decrypt(config.password)
        return config

    @staticmethod
    def send(email_info: dict):
        """
        :param email_info: {"receivers": [], "subject": "", "content": ""}
        """
        config = ToolEmailConfigService.find()
        receivers = email_info["receivers"]  # 接收邮件
        # 3个参数：文本内容/设置文本格式html/设置编码utf-8
        message = MIMEText(email_info["content"], 'html', 'utf-8')
        message['From'] = formataddr([config.user.split('@')[0], config.from_user])  # 发送者
        message['To'] = "".join(receivers)  # 接收者
        message['Subject'] = Header(email_info["subject"], 'utf-8')
        server = None
        try:
            server = smtplib.SMTP_SSL(host=config.host, port=config.port)
            server.login(config.user, config.password)
            server.sendmail(config.from_user, receivers, message.as_string())
        except smtplib.SMTPException:
            traceback.print_exc()
        finally:
            if server:
                server.quit()

    @staticmethod
    def update(curr_config: ToolEmailConfig):
        if curr_config.config_id:
            old_config = ToolEmailConfig.query.filter(
                ToolEmailConfig.config_id == curr_config.config_id).one_or_none()
            if old_config is None:
                old_config = ToolEmailConfig()
            else:
                old_config.config_id = curr_config.config_id
        else:
            old_config = ToolEmailConfig()
        old_config.from_user = curr_config.from_user
        old_config.host = curr_config.host
        old_config.password = des_encrypt(curr_config.password)
        old_config.port = curr_config.port
        old_config.user = curr_config.user
        if not curr_config.config_id:
            old_config.config_id = 1
            db.session.add(old_config)
        db.session.commit()


class PictureService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        filename = kwargs.get('filename')
        username = kwargs.get('username')
        create_times = kwargs.get('createTime')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, tool_picture_fields, Picture)
        query = []
        if filename:
            query.append(Picture.filename.like(f'%{filename}%'))
        if username:
            query.append(Picture.username.like(f'%{username}%'))
        if create_times and len(create_times) >= 2:
            query.append((Picture.create_time.between(create_times[0], create_times[1])))
        return Picture.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                            error_out=False)

    @staticmethod
    def create(curr_picture: Picture):
        exist_md5code = Picture.query.filter(Picture.md5code == curr_picture.md5code).one_or_none()
        if exist_md5code:
            raise AppException(f'{curr_picture.md5code}已存在!')
        curr_picture.create_time = datetime.datetime.now()
        db.session.add(curr_picture)
        db.session.commit()

    @staticmethod
    def find_by_md5(md5: str):
        exist_md5code = Picture.query.filter(Picture.md5code == md5).one_or_none()
        return exist_md5code

    @staticmethod
    def save(pictures: list):
        if pictures:
            url_list = [p.url for p in pictures]
            exist_list = Picture.query.filter(Picture.url.in_(url_list)).all()
            exist_urls = [p.url for p in exist_list]
            is_add = False
            for p in pictures:
                if p.url not in exist_urls:
                    p.username = "System Sync"
                    p.size = api_utils.get_size(p.size)
                    p.create_time = datetime.datetime.now()
                    db.session.add(p)
                    is_add = True
            if is_add:
                db.session.commit()

    @staticmethod
    def update(curr_picture: Picture):
        exist_picture = Picture.query.filter(Picture.md5code == curr_picture.md5code).all()
        if [old for old in exist_picture if old.picture_id != curr_picture.picture_id]:
            raise AppException(f'{curr_picture.md5code}已存在!')
        old_picture = Picture.query.filter(Picture.picture_id == curr_picture.picture_id).one_or_none()
        if old_picture is None:
            raise AppException(f'修改的数据可能已不存在!')

        old_picture.picture_id = curr_picture.picture_id
        old_picture.filename = curr_picture.filename
        old_picture.md5code = curr_picture.md5code
        old_picture.size = curr_picture.size
        old_picture.url = curr_picture.url
        old_picture.delete_url = curr_picture.delete_url
        old_picture.height = curr_picture.height
        old_picture.width = curr_picture.width
        old_picture.username = curr_picture.username
        old_picture.update_time = datetime.datetime.now()
        old_picture.update_by = curr_picture.update_by
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            picture_list = db.session.query(Picture).filter(Picture.picture_id.in_(ids)).all()
            for d in picture_list:
                if d.delete_url:
                    requests.get(d.delete_url)
                db.session.delete(d)
            db.session.commit()

    @staticmethod
    def download(data_list: list):
        contents = []
        for d in data_list:
            data = OrderedDict()
            data["文件名"] = d.filename
            data["图片地址"] = d.url
            data["图片大小"] = d.size
            data["操作人"] = d.username
            data["高度"] = d.height
            data["宽度"] = d.width
            data["删除地址"] = d.delete_url
            data["创建日期"] = format_date(d.create_time) if d.create_time else ""
            contents.append(data)
        return download_excel(contents)


class ToolLocalStorageService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, tool_local_storage_fields, ToolLocalStorage)
        blurry = kwargs.get('blurry')
        create_times = kwargs.get('createTime')
        query = []
        if blurry:
            query.append(or_(ToolLocalStorage.name.like(f'%{blurry}%'), ToolLocalStorage.suffix.like(f'%{blurry}%'),
                             ToolLocalStorage.type.like(f'%{blurry}%'), ToolLocalStorage.create_by.like(f'%{blurry}%'),
                             ToolLocalStorage.size.like(f'%{blurry}%')))
        if create_times and len(create_times) >= 2:
            query.append((ToolLocalStorage.create_time.between(create_times[0], create_times[1])))
        return ToolLocalStorage.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                                     error_out=False)

    @staticmethod
    def create(curr_tool: ToolLocalStorage):
        curr_tool.create_time = datetime.datetime.now()
        db.session.add(curr_tool)
        db.session.commit()

    @staticmethod
    def update(curr_tool: ToolLocalStorage):
        old_tool = ToolLocalStorage.query.filter(
            ToolLocalStorage.storage_id == curr_tool.storage_id).one_or_none()
        if old_tool is None:
            raise AppException(f'修改的数据可能已不存在!')

        old_tool.storage_id = curr_tool.storage_id
        old_tool.real_name = curr_tool.real_name
        old_tool.name = curr_tool.name
        old_tool.suffix = curr_tool.suffix
        old_tool.path = curr_tool.path
        old_tool.type = curr_tool.type
        old_tool.size = curr_tool.size
        old_tool.update_by = curr_tool.update_by
        old_tool.update_time = datetime.datetime.now()
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            old_list = db.session.query(ToolLocalStorage).filter(ToolLocalStorage.storage_id.in_(ids)).all()
            for d in old_list:
                if os.path.exists(d.path):
                    os.remove(d.path)
                db.session.delete(d)
            db.session.commit()

    @staticmethod
    def download(data_list: list):
        contents = []
        for d in data_list:
            data = OrderedDict()
            data["文件名"] = d.real_name
            data["备注名"] = d.name
            data["文件类型"] = d.type
            data["文件大小"] = d.size
            data["创建者"] = d.create_by
            data["创建日期"] = format_date(d.create_time) if d.create_time else ""
            contents.append(data)
        return download_excel(contents)


class ToolQiniuContentService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, tool_qiniu_content_fields, ToolQiniuContent)
        query = []
        key = kwargs.get('key')
        if key:
            query.append(ToolQiniuContent.name.like(f'%{key}%'))
        create_times = kwargs.get('createTime')
        if create_times and len(create_times) >= 2:
            query.append((ToolQiniuContent.updateTime.between(create_times[0], create_times[1])))
        return ToolQiniuContent.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                                     error_out=False)

    @staticmethod
    def create(curr_data: ToolQiniuContent):
        exist_name = ToolQiniuContent.query.filter(ToolQiniuContent.name == curr_data.name).one_or_none()
        if exist_name:
            raise AppException(f'{curr_data.name}已存在!')
        curr_data.create_time = datetime.datetime.now()
        db.session.add(curr_data)
        db.session.commit()

    @staticmethod
    def find_by_name(name: str):
        exist_name = ToolQiniuContent.query.filter(ToolQiniuContent.name == name).one_or_none()
        return exist_name

    @staticmethod
    def update(curr_data: ToolQiniuContent):
        exist_data = ToolQiniuContent.query.filter(ToolQiniuContent.name == curr_data.name).all()
        if [old for old in exist_data if old.content_id != curr_data.content_id]:
            raise AppException(f'{curr_data.name}已存在!')
        old_data = ToolQiniuContent.query.filter(ToolQiniuContent.content_id == curr_data.content_id).one_or_none()
        if old_data is None:
            raise AppException(f'修改的数据可能已不存在!')

        old_data.content_id = curr_data.content_id
        old_data.bucket = curr_data.bucket
        old_data.name = curr_data.name
        old_data.size = curr_data.size
        old_data.type = curr_data.type
        old_data.url = curr_data.url
        old_data.suffix = curr_data.suffix
        old_data.update_time = curr_data.update_time
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            old_list = db.session.query(ToolQiniuContent).filter(ToolQiniuContent.content_id.in_(ids)).all()
            for d in old_list:
                db.session.delete(d)
            db.session.commit()

    @staticmethod
    def download(data_list: list):
        contents = []
        for d in data_list:
            data = OrderedDict()
            data["文件名"] = d.name
            data["文件类型"] = d.suffix
            data["空间名称"] = d.bucket
            data["文件大小"] = d.size
            data["空间类型"] = d.type
            data["创建日期"] = format_date(d.update_time) if d.update_time else ""
            contents.append(data)
        return download_excel(contents)

    @staticmethod
    def config(curr_data: ToolQiniuConfig):
        curr_data.config_id = 1
        old_data = ToolQiniuConfig.query.filter(ToolQiniuConfig.config_id == curr_data.config_id).one_or_none()
        if old_data:
            old_data.access_key = curr_data.access_key
            old_data.bucket = curr_data.bucket
            old_data.host = curr_data.host
            old_data.secret_key = curr_data.secret_key
            old_data.type = curr_data.type
            old_data.zone = curr_data.zone
        else:
            db.session.add(curr_data)
        db.session.commit()

    @staticmethod
    def find() -> ToolQiniuConfig:
        old_data = ToolQiniuConfig.query.filter(ToolQiniuConfig.config_id == 1).one_or_none()
        return old_data if old_data else ToolQiniuConfig()

    @staticmethod
    def update_config(curr_data: ToolQiniuConfig):
        old_data = ToolQiniuConfig.query.filter(ToolQiniuConfig.type == curr_data.type).one_or_none()
        if old_data:
            old_data.access_key = curr_data.access_key
            old_data.bucket = curr_data.bucket
            old_data.host = curr_data.host
            old_data.secret_key = curr_data.secret_key
            old_data.type = curr_data.type
            old_data.zone = curr_data.zone
            db.session.commit()
