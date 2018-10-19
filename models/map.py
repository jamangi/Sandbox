#!/usr/bin/python3
'''
    Class representing a Map
'''
from models.base_model import BaseModel
import models
import os

class Map(BaseModel):
    '''
        Definition of the Map class
    '''
    def __init__(self, *args, **kwargs):
        self.location = 'training'
        self.floor_tile = 'images/map/floor/brownfloor_2_2.png'
        self.build_functions = []
        self.cell_width = 1200
        self.cell_height = 1200
        self.map_rows = 40
        self.map_cols = 40
        self.cell_size = self.cell_width // self.map_cols
        self.spawn_point = [0,0]
        self.spawn_points = [[0,0]]
        super().__init__(*args, **kwargs)