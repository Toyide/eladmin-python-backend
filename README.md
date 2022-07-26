<h1 style="text-align: center">EL-ADMIN 后台管理系统【Python后端】</h1>


#### 简介
基于Flask、Redis、Mysql、Flask-RESTful、Flask-Session、Tornado、SQLAlchemy、APScheduler、marshmallow的前后端分离的后台管理系统

持续优化中...
部分功能如服务器监测等暂时没有测试

|     |  前端源码  |    后端原版Java源码  |
|---  |--- | --- |
|  github   |  https://github.com/elunez/eladmin-web    |  https://github.com/elunez/eladmin  |

#### 开发文档
[https://el-admin.vip](https://el-admin.vip)

#### 体验地址
[https://el-admin.vip/demo](https://el-admin.vip/demo)

#### 后端模板

Python版基于： [https://gitee.com/adyfang/SnowAdminWeb](https://gitee.com/adyfang/SnowAdminWeb)
初始模板基于： [https://github.com/elunez/eladmin](https://github.com/elunez/eladmin)


#### 安装 & 启动
```
建议python版本3.7以上
初始化MySQL： py_api.sql(settings.py中配置数据库连接)
安装Redis ：  brew install redis
启动Redis ：  redis-server
安装依赖库 ：  pip3 install -r requirements.txt
启动      ：  python3 research_main.py
```

#### 代码架构
```
- src
    - config 系统配置
	    - api_utils.py API工具模块，包含记录日志、权限验证等
	    - simhei.ttf 字体文件，用于验证码显示
    - controllers API包
	    - devops_mng 运维管理API
	    - sys_mng 系统管理API
	    - sys_monitor 系统监控API
	    - sys_tools 系统工具API
        - main_api.py rest请求公共配置(异常捕获、token续期等)
    - quartz_utils 定时任务包
    - service DAO接口
	- dto_mapper.py flask-restful Model定义，用于返回前端结果(SQLAlchemy Model)的序列化
	- extensions.py 扩展(异常、redis等封装)
	- models.py 定义DB结构的SQLAlchemy Model
	- schema.py 序列化/反序列化Marshmallow Schema
	- quartz_job_test.py 定时任务测试模块，实际使用根据业务定义
	- settings.py 系统初始化配置
	- tools.py 通用工具模块(加密、生成验证码等)
- main.py 系统入口
- py_api.sql 数据库初始化脚本
```

#### 特别鸣谢

- 感谢 [AdyFang](https://gitee.com/adyfang)大佬提供的[SnowAdminWeb](https://gitee.com/adyfang/SnowAdminWeb)项目
