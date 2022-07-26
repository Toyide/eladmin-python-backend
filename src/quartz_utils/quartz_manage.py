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

# @Time    : 2022/7/11 18:14
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : quartz_manage.py
# @Project : eladmin_py_backend
import datetime

from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.triggers.cron import CronTrigger
from flask_apscheduler import APScheduler
from peak.util.proxies import CallbackProxy, get_callback

from src.extensions import AppException
from src.models import QuartzJob, QuartzLog, db
from src.quartz_utils.quartz_runnable import QuartzRunnable

JOB_NAME = "TASK_"
# scheduler = BackgroundScheduler()  # 定时任务调度，调度器在后台线程中运行，不会阻塞当前线程
# scheduler = TornadoScheduler()  # 定时任务调度，Tornado的IO模型。
scheduler = APScheduler()  # 定时任务调度，带app上下文


def check_cron(cron: str):
    try:
        CronTrigger.from_crontab(cron)
    except:
        raise AppException("cron表达式格式错误!")


def add_job_log(curr_data: QuartzLog):
    with scheduler.app.app_context():
        db.session.add(curr_data)
        db.session.commit()
        db.session.close()


def exec_job(quartz_job: QuartzJob):
    quartz_log = QuartzLog()
    quartz_log.create_time = datetime.datetime.now()
    start_time = datetime.datetime.now()
    try:
        quartz_log.job_name = quartz_job.job_name
        quartz_log.bean_name = quartz_job.bean_name
        quartz_log.method_name = quartz_job.method_name
        quartz_log.params = quartz_job.params
        quartz_log.cron_expression = quartz_job.cron_expression
        job_thread = QuartzRunnable(quartz_job.bean_name, quartz_job.method_name, quartz_job.params)
        job_thread.start()
        job_thread.join()
        quartz_log.is_success = True
        cost = (datetime.datetime.now() - start_time).microseconds / 1000
        quartz_log.log_time = cost
    except Exception as e:
        quartz_log.exception_detail = str(e)
        cost = (datetime.datetime.now() - start_time).microseconds / 1000
        quartz_log.log_time = cost
        quartz_log.is_success = False

    proxy = CallbackProxy(add_job_log)
    get_callback(proxy)(quartz_log)


def add_job(quartz_job: QuartzJob, is_run_now=False):
    if is_run_now:
        scheduler.add_job(func=exec_job,
                          args=(quartz_job,),
                          next_run_time=datetime.datetime.now(),
                          trigger=None,
                          id=f'{JOB_NAME}{quartz_job.job_id}',
                          name=quartz_job.description)
    else:
        scheduler.add_job(func=exec_job,
                          args=(quartz_job,),
                          trigger=CronTrigger.from_crontab(quartz_job.cron_expression),
                          id=f'{JOB_NAME}{quartz_job.job_id}',
                          name=quartz_job.description)


def run_job_now(quartz_job: QuartzJob):
    job_key = f'{JOB_NAME}{quartz_job.job_id}'
    exist_job = scheduler.get_job(job_key)
    if exist_job is None:
        add_job(quartz_job, True)
    if scheduler.state != STATE_RUNNING:
        scheduler.start()


def delete_jobs(ids: list):
    for d in ids:
        job_key = f'{JOB_NAME}{d}'
        exist_job = scheduler.get_job(job_key)
        if exist_job:
            scheduler.remove_job(job_key)


def resume_job(quartz_job: QuartzJob):
    job_key = f'{JOB_NAME}{quartz_job.job_id}'
    exist_job = scheduler.get_job(job_key)
    if exist_job is None:
        add_job(quartz_job)
    scheduler.resume_job(job_key)
    if scheduler.state != STATE_RUNNING:
        scheduler.start()


def pause_job(quartz_job: QuartzJob):
    job_key = f'{JOB_NAME}{quartz_job.job_id}'
    exist_job = scheduler.get_job(job_key)
    if exist_job is None:
        add_job(quartz_job)
    scheduler.pause_job(job_key)
    if scheduler.state != STATE_RUNNING:
        scheduler.start()
