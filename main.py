#!/usr/bin/env python

import os

import tornado
from flask_script import Manager, Server
from flask_script.commands import ShowUrls, Clean
from tornado import httpserver
from tornado.options import define, options
from tornado.wsgi import WSGIContainer

from src import create_app
from src.models import db

# default to dev config because no one should use this in
# production anyway
define("port", default=8000, help="py-api running on this port", type=int)
env = os.environ.get('src_ENV', 'dev')
app = create_app('src.settings.%sConfig' % env.capitalize())

manager = Manager(app)
manager.add_command("server", Server())
manager.add_command("show-urls", ShowUrls())
manager.add_command("clean", Clean())


@manager.shell
def make_shell_context():
    """ Creates a python REPL with several default imports
        in the context of the app
    """

    return dict(app=app, db=db)


@manager.command
def createdb():
    """ Creates a database with all of the tables defined in
        your SQLAlchemy models
    """
    # db.create_all()


if __name__ == "__main__":
    # manager.run()

    # print(app.url_map)
    app.run(host='0.0.0.0', port='5003')
    tornado.options.parse_command_line()
    # http_server = tornado.httpserver.HTTPServer(application)
    http_server = httpserver.HTTPServer(WSGIContainer(app))
    http_server.listen(port=options.port, address='0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()
