# -*- coding: utf-8 -*-
from . import home

@home.route('/')
def index():
    return 'hello, home page '
