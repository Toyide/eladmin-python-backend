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

# @Time    : 2022/8/16 20:55
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : quartz_service.py
# @Project : eladmin_py_backend
import datetime

from src.config import api_utils
from src.dto_mapper import quartz_job_fields, quartz_log_fields
from src.extensions import AppException
from src.models import QuartzJob, db, QuartzLog
from src.quartz_utils import quartz_manage
from src.quartz_utils.quartz_manage import check_cron


class QuartzJobService:
    @staticmethod
    def query_all(page=0, size=9999, **kwargs):
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, quartz_job_fields, QuartzJob)
        job_name = kwargs.get('jobName')
        create_times = kwargs.get('createTime')
        query = []
        if job_name:
            query.append(QuartzJob.job_name.like(f'%{job_name}%'))
        if create_times and len(create_times) >= 2:
            query.append((QuartzJob.create_time.between(create_times[0], create_times[1])))
        return QuartzJob.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                              error_out=False)

    @staticmethod
    def query_all_log(page=0, size=9999, **kwargs):
        sorts = kwargs.get('sort')
        sort_params = api_utils.build_sorts(sorts, quartz_log_fields, QuartzLog)
        job_name = kwargs.get('jobName')
        is_success = kwargs.get('isSuccess')
        create_times = kwargs.get('createTime')
        query = []
        if job_name:
            query.append(QuartzLog.job_name.like(f'%{job_name}%'))
        if is_success:
            query.append((QuartzLog.is_success.is_(True if is_success == 'true' else False)))
        if create_times and len(create_times) >= 2:
            query.append((QuartzLog.create_time.between(create_times[0], create_times[1])))
        return QuartzLog.query.filter(*query).order_by(*sort_params).paginate(int(page) + 1, per_page=int(size),
                                                                              error_out=False)

    @staticmethod
    def find_by_id(job_id: int) -> QuartzJob:
        quartz_job = QuartzJob.query.filter(QuartzJob.job_id == job_id).one_or_none()
        if quartz_job is None:
            raise AppException(f'您所操作的对象已不存在!')
        return quartz_job

    @staticmethod
    def create(curr_quartz_job: QuartzJob):
        check_cron(curr_quartz_job.cron_expression)
        db.session.add(curr_quartz_job)
        db.session.commit()

    @staticmethod
    def update(curr_quartz_job: QuartzJob):
        if curr_quartz_job.sub_task and curr_quartz_job.job_id in curr_quartz_job.sub_task.split(","):
            raise AppException(f'子任务中不能添加当前任务!')
        old_job = QuartzJob.query.filter(QuartzJob.job_id == curr_quartz_job.job_id).one_or_none()
        if old_job is None:
            raise AppException(f'修改的数据可能已不存在!')
        old_job.bean_name = curr_quartz_job.bean_name
        old_job.cron_expression = curr_quartz_job.cron_expression
        old_job.job_name = curr_quartz_job.job_name
        old_job.method_name = curr_quartz_job.method_name
        old_job.params = curr_quartz_job.params
        old_job.description = curr_quartz_job.description
        old_job.person_in_charge = curr_quartz_job.person_in_charge
        old_job.email = curr_quartz_job.email
        old_job.sub_task = curr_quartz_job.sub_task
        old_job.pause_after_failure = curr_quartz_job.pause_after_failure
        old_job.update_time = datetime.datetime.now()
        old_job.update_by = curr_quartz_job.update_by
        db.session.commit()

    @staticmethod
    def delete(ids: list):
        if ids:
            quartz_manage.delete_jobs(ids)
            db.session.query(QuartzJob).filter(QuartzJob.job_id.in_(ids)).delete(synchronize_session=False)
            db.session.commit()

    @staticmethod
    def execution(quartz_job: QuartzJob):
        check_cron(quartz_job.cron_expression)
        quartz_manage.run_job_now(quartz_job)

    @staticmethod
    def update_job(quartz_job: QuartzJob):
        if quartz_job.is_pause[0]:
            quartz_manage.resume_job(quartz_job)
            quartz_job.is_pause = False
        else:
            quartz_manage.pause_job(quartz_job)
            quartz_job.is_pause = True
        db.session.commit()
