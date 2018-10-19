#!/usr/bin/python3
'''
    Class representing a Script
'''
from models.base_model import BaseModel
import models
import os

class Script(BaseModel):
    '''
        Definition of the Script class
    '''
    def __init__(self, *args, **kwargs):
        self.user_id = ''
        self.material = 0
        self.location = 'training'
        self.filename = ''
        self.filetext = ''
        self.filetype = 'bash'
        self.row = 0
        self.col = 0
        self.collected_list = {}
        super().__init__(*args, **kwargs)

    def has_collected(self, user_id):
        if self.collected_list.get(user_id) is None:
            return False
        else:
            return True

    def collect(self, user_id):
        self.collected_list[user_id] = True
        self.save()

    @staticmethod
    def get_scripts(location=None):
        all_scripts = models.storage.all('Script')
        res = []
        for script in all_scripts.values():
            if location is None:
                res.append(script)
            else:
                if location == script.location:
                    res.append(script)
        return res
