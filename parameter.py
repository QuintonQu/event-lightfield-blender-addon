import bpy
from . import render

def register():
    bpy.utils.register_class(LFProperty)
    bpy.utils.register_class(LF_PT_Panel)
    lf = bpy.props.PointerProperty(type=LFProperty)
    bpy.types.Object.lightfield = lf

def unregister():
    bpy.utils.unregister_class(LFProperty)
    bpy.utils.unregister_class(LF_PT_Panel)
    del bpy.types.Object.lightfield

# def base_x(self):
#     if self.plane:
#         return self.plane.scale[0] / max(1, self.num_cols-1)
#     else:
#         return 0.0
    
# def set_base_x(self, x):
#     self.plane.scale[0] = x * max(1, self.num_cols-1)

# def update_cols(self, context):
#     self.plane.scale[0] = self.base_x * max(1, self.num_cols-1)

# def base_y(self):
#     if self.plane:
#         return self.plane.scale[1] / max(1, self.num_rows-1)
#     else:
#         return 0.0
    
# def set_base_y(self, y):
#     self.plane.scale[1] = y * max(1, self.num_rows-1)

# def update_rows(self, context):
#     self.plane.scale[0] = self.base_y * max(1, self.num_rows-1)



class LFProperty(bpy.types.PropertyGroup):
    num_rows : bpy.props.IntProperty(
        name='rows',
        default=1,
        soft_min=0,
        description='number of rows of the camera array')
    
    num_cols : bpy.props.IntProperty(
        name='cols',
        default=1,
        soft_min=0,
        description='number of columns of the camera array')
    
    base_x : bpy.props.FloatProperty(
        name='total x',
        soft_min=0,
        default=0.1,
        precision=4,
        description='the x baseline between each camera')
    
    base_y : bpy.props.FloatProperty(
        name='total y',
        soft_min=0,
        default=0.1,
        precision=4,
        description='the y baseline distance between each camera')
    
    threshold : bpy.props.FloatProperty(
        name='threshold',
        soft_min=0,
        default=0.1,
        description='the threshold for transition from linear to log mapping')
    
    frequency : bpy.props.FloatProperty(
        name='frequency',
        soft_min=0,
        default=10,
        description='the frequency of the light field')
    


class LF_PT_Panel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_EventLightfieldPanel'
    bl_label = 'Event Light Field'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    # def draw_header(self, ctx):
    #     layout = self.layout
    #     lf = ctx.object.lightfield
    #     layout.prop(lf, 'enabled', text='', toggle=False)

    def draw(self, ctx):
        # default spec
        layout = self.layout
        lf = ctx.object.lightfield
        row = layout.row(align=True)
        row.prop(lf, 'num_cols')
        row.prop(lf, 'num_rows')
        row = layout.row(align=True)
        row.prop(lf, 'base_x')
        row.prop(lf, 'base_y')
        row = layout.row(align=True)
        row.prop(lf, 'threshold')
        row.prop(lf, 'frequency')
        layout.separator()
        layout.operator(
            render.SimpleRender.bl_idname,
            text=render.SimpleRender.bl_label,
            icon='RENDER_STILL')
        layout.operator(
            render.LightFieldRender.bl_idname,
            text=render.LightFieldRender.bl_label,
            icon='RENDER_STILL')
        layout.operator(
            render.SimpleAnimation.bl_idname,
            text=render.SimpleAnimation.bl_label,
            icon='RENDER_ANIMATION')
        layout.operator(
            render.EventRender.bl_idname,
            text=render.EventRender.bl_label,
            icon='RENDER_ANIMATION')
        layout.operator(
            render.EventLightFieldRender.bl_idname,
            text=render.EventLightFieldRender.bl_label,
            icon='RENDER_ANIMATION')
        layout.operator(
            render.EventGalvoRender.bl_idname,
            text=render.EventGalvoRender.bl_label,
            icon='RENDER_ANIMATION')

    @classmethod
    def poll(cls, ctx):
        return ((ctx.object is not None)
                and ctx.object.type == 'CAMERA')



