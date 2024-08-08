bl_info = {
    "name" : "Event Light Field",
    "author" : "Quinton Qu",
    "description" : "",
    "blender" : (4, 2, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Render"
}

import bpy
from . import render
from . import parameter
from . import util

import importlib
importlib.reload(render)
importlib.reload(parameter)
importlib.reload(util)


def register():
    render.register()
    parameter.register()

def unregister():
    render.unregister()
    parameter.unregister()

