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

# @Time    : 2022/5/22 22:41
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : __init__.py.py
# @Project : eladmin_py_backend
import os
import tempfile


class ServerConfig:
    path = r'../storage/file'  # 文件存储路径
    avatar = r'../storage/avatar'  # 头像文件存储路径
    upload_dir = os.path.join(tempfile.gettempdir(), "file")  # 上传文件临时目录
    default_password = b"123456"  # 新增用户默认密码
    max_size = 100  # 文件大小 /M
    avatar_max_size = 5  # 文件大小 /M
    ip_url = r"http://whois.pconline.com.cn/ipJson.jsp?ip=%s&json=true"  # IP归属地查询
    token_validity_in_seconds = 1 * 60 * 60  # 令牌过期时间 此处单位/秒 ，默认4小时
    token_start_with = "Bearer"  # 令牌前缀
    online_key = "online-token-"  # 在线用户key
    detect = 30 * 60  # token 续期检查时间范围（默认30分钟，单位秒），在token即将过期的一段时间内用户操作了，则给用户的token续期
    renew = 1 * 60 * 60  # 续期时间范围，默认1小时，单位秒
    # 密码加密传输，前端公钥加密，后端私钥解密
    rsa_private_key = "MIIBUwIBADANBgkqhkiG9w0BAQEFAASCAT0wggE5AgEAAkEA0vfvyTdGJkdbHkB8mp0f3FE0GYP3AYPaJF7jUd1M0XxFSE2ceK3k2kw20YvQ09NJKk+OMjWQl9WitG9pB6tSCQIDAQABAkA2SimBrWC2/wvauBuYqjCFwLvYiRYqZKThUS3MZlebXJiLB+Ue/gUifAAKIg1avttUZsHBHrop4qfJCwAI0+YRAiEA+W3NK/RaXtnRqmoUUkb59zsZUBLpvZgQPfj1MhyHDz0CIQDYhsAhPJ3mgS64NbUZmGWuuNKp5coY2GIj/zYDMJp6vQIgUueLFXv/eZ1ekgz2Oi67MNCk5jeTF2BurZqNLR3MSmUCIFT3Q6uHMtsB9Eha4u7hS31tj1UWE+D+ADzp59MGnoftAiBeHT7gDMuqeJHPL4b+kC+gzV4FGTfhR9q3tTbklZkD2A=="
    login_code_expiration = 1  # 登录图形验证码有效时间/分钟
    code_expiration = 5  # 邮箱验证码有效时间/分钟
    email_reset_email_prefix = 'email_reset_email_code_'  # 通过旧邮箱重置邮箱，缓存前缀
    des_secret_key = 'Passw0rd'  # DES 秘钥，用于邮箱验证码加解密
    generator_enabled = False  # 是否允许生成代码，生产环境设置为false
    sm_ms_url = 'https://sm.ms/api'  # 免费图床
    sm_ms_token = '4FIlqA23uoF5G54Ctv7BCu7PjYKlNi4l'  # sm.ms 图床的 token，注册sm.ms后生成token
    qiniu_max_size = 15  # 七牛云 文件大小 /M
    qiniu_access_key = '1KqnTnHjd-UENtOtINXJOewKjt4uvZbeAmUkS7Wy'  # 七牛云 AccessKey
    qiniu_secret_key = '8abam0p2ADMG-GcX5hwZXF7yzdOuBQg_6v52M6t0'  # 七牛云 SecretKey
