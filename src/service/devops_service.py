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

# @Time    : 2022/7/19 19:16
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : devops_service.py
# @Project : eladmin_py_backend
import datetime
import uuid
from collections import OrderedDict

from sqlalchemy import or_

from src.config import api_utils
from src.dto_mapper import server_deploy_fields, app_fields, deploy_fields, deployhistory_fields, database_fields
from src.extensions import AppException
from src.models import MntServer, MntDeploy, MntApp, DeployServer, MntDeployHistory, db, MntDatabase
from src.tools import format_date, download_excel, connect_server


class ServerDeployService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs) -> list:
        blurry = kwargs.get('blurry')
        create_times = kwargs.get('createTime')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, server_deploy_fields, MntServer)
        query = []
        if blurry:
            query.append(or_(MntServer.name.like(f'%{blurry}%'), MntServer.ip.like(f'%{blurry}%'),
                             MntServer.account.like(f'%{blurry}%')))
        if create_times and len(create_times) >= 2:
            query.append((MntServer.create_time.between(create_times[0], create_times[1])))
        return MntServer.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                              error_out=False)

    @staticmethod
    def create(curr_data: MntServer):
        curr_data.create_time = datetime.datetime.now()
        db.session.add(curr_data)
        db.session.commit()

    @staticmethod
    def update(curr_data: MntServer):
        old_data = MntServer.query.filter(MntServer.server_id == curr_data.server_id).one_or_none()
        if old_data is None:
            raise AppException(f'修改的数据可能已不存在!')

        old_data.server_id = curr_data.server_id
        old_data.account = curr_data.account
        old_data.ip = curr_data.ip
        old_data.name = curr_data.name
        old_data.password = curr_data.password
        old_data.port = curr_data.port
        old_data.update_by = curr_data.update_by
        old_data.update_time = curr_data.update_time
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            old_list = db.session.query(MntServer).filter(MntServer.server_id.in_(ids)).all()
            for d in old_list:
                db.session.delete(d)
            db.session.commit()

    @staticmethod
    def find_by_id(server_id: int = None) -> MntServer:
        data = MntServer.query.filter(MntServer.server_id == server_id).one_or_none()
        if data is None:
            raise AppException(f'您所操作的对象已不存在!')
        return data

    @staticmethod
    def download(data_list: list):
        contents = []
        for d in data_list:
            data = OrderedDict()
            data["服务器名称"] = d.name
            data["服务器IP"] = d.ip
            data["端口"] = d.port
            data["账号"] = d.account
            data["创建时间"] = format_date(d.create_time) if d.create_time else ""
            contents.append(data)
        return download_excel(contents)

    @staticmethod
    def test_connect(curr_server: MntServer) -> bool:
        return connect_server(curr_server.ip, curr_server.port, curr_server.account, curr_server.password)


class AppService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs) -> list:
        name = kwargs.get('name')
        create_times = kwargs.get('createTime')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, app_fields, MntApp)
        query = []
        if name:
            query.append(MntApp.name.like(f'%{name}%'))
        if create_times and len(create_times) >= 2:
            query.append((MntApp.create_time.between(create_times[0], create_times[1])))
        return MntApp.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                           error_out=False)

    @staticmethod
    def create(curr_app: MntApp):
        curr_app.create_time = datetime.datetime.now()
        db.session.add(curr_app)
        db.session.commit()

    @staticmethod
    def update(curr_app: MntApp):
        old_app = MntApp.query.filter(MntApp.app_id == curr_app.app_id).one_or_none()
        if old_app is None:
            raise AppException(f'修改的数据可能已不存在!')
        old_app.name = curr_app.name
        old_app.upload_path = curr_app.upload_path
        old_app.deploy_path = curr_app.deploy_path
        old_app.backup_path = curr_app.backup_path
        old_app.port = curr_app.port
        old_app.start_script = curr_app.start_script
        old_app.deploy_script = curr_app.deploy_script
        old_app.update_time = datetime.datetime.now()
        old_app.update_by = curr_app.update_by
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            db.session.query(MntApp).filter(MntApp.app_id.in_(ids)).delete(
                synchronize_session=False)
            db.session.commit()

    @staticmethod
    def download(data_list: list):
        contents = []
        for d in data_list:
            data = OrderedDict()
            data["应用名称"] = d.name
            data["端口"] = d.port
            data["上传目录"] = d.upload_path
            data["部署目录"] = d.deploy_path
            data["备份目录"] = d.backup_path
            data["启动脚本"] = d.start_script
            data["部署脚本"] = d.deploy_script
            data["创建日期"] = format_date(d.create_time) if d.create_time else ""
            contents.append(data)
        return download_excel(contents)


class DeployService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs) -> list:
        app_name = kwargs.get('appName')
        create_times = kwargs.get('createTime')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, deploy_fields, MntDeploy)
        query = []
        if app_name:
            query.append(MntServer.name.like(f'%{app_name}%'))
        if create_times and len(create_times) >= 2:
            query.append((MntDeploy.create_time.between(create_times[0], create_times[1])))
        return MntDeploy.query.join(DeployServer).join(MntServer).filter(*query).order_by(*sort_params).paginate(
            int(page) + 1, per_page=int(size),
            error_out=False)

    @staticmethod
    def find_by_id(deploy_id: int) -> MntDeploy:
        deploy = db.session.query(MntDeploy).filter(MntDeploy.deploy_id == deploy_id).one_or_none()
        if deploy is None:
            raise AppException(f'您所操作的对象已不存在!')
        return deploy

    @staticmethod
    def deploy(file_save_path: str, deploy_id: int, username: str):
        print("部署:", file_save_path)
        deploy = DeployService.find_by_id(deploy_id=deploy_id)
        for server_deploy in deploy.deploys:
            history = MntDeployHistory()
            history.app_name = deploy.app.name
            history.deploy_user = username
            history.ip = server_deploy.ip
            history.deploy_id = deploy_id
            history.deploy_date = datetime.datetime.now()
            DeployHistoryService.create(curr_history=history)


class DeployHistoryService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs) -> list:
        blurry = kwargs.get('blurry')
        deploy_id = kwargs.get('deployId')
        deploy_date = kwargs.get('deployDate')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, deployhistory_fields, MntDeployHistory)
        query = []
        if blurry:
            query.append(or_(MntDeployHistory.app_name.like(f'%{blurry}%'), MntDeployHistory.ip.like(f'%{blurry}%'),
                             MntDeployHistory.deploy_user.like(f'%{blurry}%')))
        if deploy_id:
            query.append(MntDeployHistory.deploy_id == deploy_id)
        if deploy_date and len(deploy_date) >= 2:
            query.append((MntDeployHistory.deploy_date.between(deploy_date[0], deploy_date[1])))
        return MntDeployHistory.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                                     error_out=False)

    @staticmethod
    def create(curr_history: MntDeployHistory):
        curr_history.history_id = str(uuid.uuid1())
        db.session.add(curr_history)
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            db.session.query(MntDeployHistory).filter(MntDeployHistory.history_id.in_(ids)).delete(
                synchronize_session=False)
            db.session.commit()


class DatabaseService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs) -> list:
        blurry = kwargs.get('blurry')
        jdbc_url = kwargs.get('jdbcUrl')
        create_times = kwargs.get('createTime')
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, database_fields, MntDatabase)
        query = []
        if blurry:
            query.append(MntDatabase.name.like(f'%{blurry}%'))
        if jdbc_url:
            query.append(MntDatabase.jdbc_url == jdbc_url)
        if create_times and len(create_times) >= 2:
            query.append((MntDatabase.create_time.between(create_times[0], create_times[1])))
        return MntDatabase.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                                error_out=False)

    @staticmethod
    def find_by_id(db_id: str) -> MntDatabase:
        database = db.session.query(MntDatabase).filter(MntDatabase.db_id == db_id).one_or_none()
        if database is None:
            raise AppException(f'您所操作的对象已不存在!')
        return database

    @staticmethod
    def create(curr_db: MntDatabase):
        curr_db.db_id = str(uuid.uuid1())
        curr_db.create_time = datetime.datetime.now()
        db.session.add(curr_db)
        db.session.commit()

    @staticmethod
    def update(curr_db: MntDatabase):
        database = MntDatabase.query.filter(MntDatabase.db_id == curr_db.db_id).one_or_none()
        if database is None:
            raise AppException(f'修改的数据可能已不存在!')
        database.name = curr_db.name
        database.jdbc_url = curr_db.jdbc_url
        database.user_name = curr_db.user_name
        database.pwd = curr_db.pwd
        database.update_time = datetime.datetime.now()
        database.update_by = curr_db.update_by
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            db.session.query(MntDatabase).filter(MntDatabase.db_id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()

    @staticmethod
    def test_connect(curr_db: MntDatabase):
        return api_utils.test_connect(curr_db)
