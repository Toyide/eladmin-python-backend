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
# @Time    : 2022/5/20 20:36
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : tools.py
# @Project : eladmin_py_backend
import base64
import datetime
import random
import re
import traceback
import uuid
from io import BytesIO

import bcrypt
import paramiko
import xlsxwriter
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from flask import make_response
from pyDes import des, CBC, PAD_PKCS5

from src import ServerConfig

init_chars = 'QWERTYUIOPASDFGHJKLZXCVBNM'  # 生成允许的字符集合
default_font = "src/config/simhei.ttf"  # 验证码字体


def random_code(chars=init_chars, length=4):
    return random.sample(chars, length)


# 生成验证码接口
def verify_image(size=(111, 50),
                 img_type="PNG",
                 mode="RGB",
                 bg_color=(255, 255, 255),
                 fg_color=(0, 0, 255),
                 font_size=20,
                 font_type=default_font,
                 draw_lines=True,
                 n_line=(1, 1),
                 draw_points=True,
                 point_chance=1):
    """
    生成验证码图片
    :param size: 图片的大小，格式（宽，高），默认为(111, 36)
    :param chars: 允许的字符集合，格式字符串
    :param img_type: 图片保存的格式，默认为PNG，可选的为GIF，JPEG，TIFF，PNG
    :param mode: 图片模式，默认为RGB
    :param bg_color: 背景颜色，默认为白色
    :param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
    :param font_size: 验证码字体大小
    :param font_type: 验证码字体
    :param length: 验证码字符个数
    :param draw_lines: 是否划干扰线
    :param n_line: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
    :param draw_points: 是否画干扰点
    :param point_chance: 干扰点出现的概率，大小范围[0, 100]
    :return: [0]: 验证码字节流, [1]: 验证码图片中的字符串
    """

    width, height = size  # 宽， 高
    img = Image.new(mode, size, bg_color)  # 创建图形
    draw = ImageDraw.Draw(img)  # 创建画笔

    def create_strs():
        """
        绘制验证码字符
        """
        c_chars = random_code()
        codes = f' {" ".join(c_chars)} '
        font = ImageFont.truetype(font_type, font_size)
        # font = ImageFont.load_default().font
        font_width, font_height = font.getsize(codes)
        draw.text(((width - font_width) / 3, (height - font_height) / 3),
                  codes, font=font, fill=fg_color)
        return ''.join(c_chars)

    if draw_lines:
        # 绘制干扰线
        line_num = random.randint(*n_line)  # 干扰线条数
        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            # 结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))
    if draw_points:
        # 绘制干扰点
        chance = min(100, max(0, int(point_chance)))  # 大小限制在[0, 100]
        for w in range(width):
            for h in range(height):
                tmp = random.randint(0, 100)
                if tmp > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    codes = create_strs()
    # 图形扭曲参数
    params = [1 - float(random.randint(1, 2)) / 100,
              0,
              0,
              0,
              1 - float(random.randint(1, 10)) / 100,
              float(random.randint(1, 2)) / 500,
              0.001,
              float(random.randint(1, 2)) / 500
              ]
    img = img.transform(size, Image.PERSPECTIVE, params)  # 创建扭曲
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 滤镜，边界加强（阈值更大）
    bio = BytesIO()
    img.save(bio, img_type)
    img_str = b"data:image/png;base64," + base64.b64encode(bio.getvalue())
    return codes, img_str.decode('utf-8')


def base64_to_image(base64_str, image_path=None):
    base64_data = re.sub('^data:image/.+;base64,', '', base64_str)
    byte_data = base64.b64decode(base64_data)
    image_data = BytesIO(byte_data)
    img = Image.open(image_data)
    if image_path:
        img.save(image_path)
    return img


def decrypt_by_private_key(private_key: str, data: str) -> bytes:
    """
    私钥解密
    :param private_key: 配置的私钥
    :param data: 待解密的密文
    :return: 解密后的明文
    """
    byte_data = base64.b64decode(private_key)
    rsa_key = RSA.importKey(byte_data)
    cipher = PKCS1_v1_5.new(rsa_key)
    random_data = Random.new().read
    text = cipher.decrypt(base64.b64decode(data), random_data)
    return text


def check_password(password: bytes, hashed: bytes) -> bool:
    """
    校验密码
    :param password: 密码明文
    :param hashed: 密文(DB中保存的password)
    :return: bool
    """
    return bcrypt.checkpw(password, hashed)


def format_date(d: datetime) -> str:
    return datetime.datetime.strftime(d, '%Y-%m-%d %H:%M:%S')


def trim_and_lower(p: str) -> str:
    return p.strip().lower() if p else ""


def download_excel(contents: list):
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
    sheet = workbook.add_worksheet(u'sheet1')
    style = workbook.add_format()
    for i, data in enumerate(contents):
        if i == 0:
            for j, (k, _) in enumerate(data.items()):
                sheet.write(i, j, k, style)
        for p, (_, v) in enumerate(data.items()):
            sheet.write(i + 1, p, v, style)
    workbook.close()
    buffer.seek(0)
    file_name = str(uuid.uuid1()) + ".xlsx"
    rsp = make_response(buffer.getvalue())
    rsp.headers["Content-Disposition"] = "attachment; filename={}.xlsx".format(
        file_name)
    rsp.headers['Content-Type'] = 'application/x-xlsx'
    return rsp


def des_encrypt(password):
    des_iv = ServerConfig.des_secret_key
    des_obj = des(ServerConfig.des_secret_key, CBC, des_iv,
                  padmode=PAD_PKCS5)  # 秘钥，加密方式，自定IV向量，填充方式
    secret_bytes = des_obj.encrypt(password.encode())
    return base64.b64encode(secret_bytes).decode()


def des_decrypt(password):
    des_iv = ServerConfig.des_secret_key
    des_obj = des(ServerConfig.des_secret_key, CBC, des_iv, padmode=PAD_PKCS5)
    pass_bytes = des_obj.decrypt(base64.b64decode(password))
    return pass_bytes.decode()


def connect_server(ip, port, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())  # know_hosts文件中的主机
        ssh.connect(hostname=ip, port=port,
                    username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command('ls')
        res, err = stdout.read(), stderr.read()
        result = res if res else err
        print(result)
        ssh.close()  # 关闭连接
    except Exception as e:
        traceback.print_exc()
        return False
    return True
