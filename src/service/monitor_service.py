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

# @Time    : 2022/7/19 12:51
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : monitor_service.py
# @Project : eladmin_py_backend
import datetime
import json
import platform

import psutil

from src import redis_client, ServerConfig
from src.config import api_utils


class OnlineUserService:
    @staticmethod
    def query_all(page=0, size=10, **kwargs) -> list:
        _filter = kwargs.get('filter')
        online_users = OnlineUserService.get_all(filter_key=_filter)
        p = int(page) + 1
        s = int(size)
        return online_users[int(page) * s:p * s]

    @staticmethod
    def get_all(filter_key: str = None) -> list:
        online_users = []
        for key in redis_client.scan_iter(f"{ServerConfig.online_key}*"):
            user_str = redis_client.get(key)
            user = json.loads(user_str)
            if filter_key:
                if filter_key in str(user):
                    online_users.append(user)
            else:
                online_users.append(user)
        return online_users

    @staticmethod
    def check_online_user(username: str, igore_token: str):
        users = OnlineUserService.get_all(filter_key=username)
        for user in users:
            if igore_token and igore_token != user["key"] and user["username"] == username:
                OnlineUserService.kick_out(key=user["key"])

    @staticmethod
    def kick_out(key: str):
        k = f'{ServerConfig.online_key}{key}'
        if redis_client.exists(k):
            redis_client.delete(k)


class MonitorService:
    @staticmethod
    def get_servers() -> dict:
        rs = {"sys": MonitorService.get_system_info(),  # 系统信息
              "cpu": MonitorService.get_cpu_info(),  # cpu 信息
              "memory": MonitorService.get_memory_info(),  # 内存信息
              "swap": MonitorService.get_swap_info(),  # 交换区信息
              "disk": MonitorService.get_disk_info(),  # 磁盘
              "time": datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S')}
        return rs

    @staticmethod
    def get_system_info() -> dict:
        def get_ip():
            netcard_info = []
            info = psutil.net_if_addrs()
            for k, v in info.items():
                for item in v:
                    if item[0] == 2 and not item[1] == '127.0.0.1':
                        netcard_info.append(item[1])
            return "".join(netcard_info)

        rs = {"os": f'{platform.system()}{platform.version()}', "day": "", "ip": get_ip()}
        return rs

    @staticmethod
    def get_cpu_info() -> dict:
        phy_count = psutil.cpu_count(logical=False)
        logic_count = psutil.cpu_count()
        # 当前可用cpu个数
        idle_total = len(psutil.Process().cpu_affinity())
        rs = {"name": '', "package": f"{phy_count}个物理CPU", "core": logic_count, "coreNumber": logic_count,
              "logic": logic_count, "used": psutil.cpu_percent(),
              "idle": idle_total}
        return rs

    @staticmethod
    def get_memory_info() -> dict:
        mem = psutil.virtual_memory()
        rs = {"total": api_utils.get_size(mem.total), "available": api_utils.get_size(mem.available),
              "used": api_utils.get_size(mem.used), "usageRate": mem.percent}
        return rs

    @staticmethod
    def get_swap_info() -> dict:
        swap = psutil.swap_memory()
        rs = {"total": api_utils.get_size(swap.total), "available": api_utils.get_size(swap.free),
              "used": api_utils.get_size(swap.used), "usageRate": swap.percent}
        return rs

    @staticmethod
    def get_disk_info() -> dict:
        disk = psutil.disk_partitions()
        total = 0
        used = 0
        for d in disk:
            if d.fstype:
                disk_usage = psutil.disk_usage(d.mountpoint)
                total += disk_usage.total
                used += disk_usage.used
        rs = {"total": api_utils.get_size(total), "available": api_utils.get_size(total - used),
              "used": api_utils.get_size(used), "usageRate": round((used / total) * 100, 2)}
        return rs
