#!/usr/bin/python3
'''
    Package initializer
'''

from models.base_model import BaseModel
from models.user import User
from models.script import Script
from models.map import Map
from models.engine.file_storage import FileStorage

classes = {"User": User, "BaseModel": BaseModel, "Script": Script, "Map": Map}

storage = FileStorage()
storage.reload()