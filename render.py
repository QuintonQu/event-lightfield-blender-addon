import bpy
import os
from . import util
import numpy as np
from mathutils import Vector, Matrix

def register():
    bpy.utils.register_class(SimpleRender)
    bpy.utils.register_class(LightFieldRender)
    bpy.utils.register_class(SimpleAnimation)
    bpy.utils.register_class(EventRender)
    bpy.utils.register_class(EventLightFieldRender)
    bpy.utils.register_class(EventGalvoRender)

def unregister():
    bpy.utils.unregister_class(SimpleRender)
    bpy.utils.unregister_class(LightFieldRender)
    bpy.utils.unregister_class(SimpleAnimation)
    bpy.utils.unregister_class(EventRender)
    bpy.utils.unregister_class(EventLightFieldRender)
    bpy.utils.unregister_class(EventGalvoRender)


class SimpleRender(bpy.types.Operator):
    bl_idname = "render.simple_render"
    bl_label = "Simple Render"

    def execute(self, context):
        # Set the render output path
        # bpy.context.scene.render.filepath += 'simple_render.png'
        # Render the image
        bpy.ops.render.render(write_still=True)
        return {'FINISHED'}
    
class SimpleAnimation(bpy.types.Operator):
    bl_idname = "render.simple_animation"
    bl_label = "Simple Animation"

    def pre(self, scene, *args):
        print(f'render on frame {self.current_frame:04d}')
        bpy.context.scene.render.filepath = self.path + self.output_dir + f'frame_{self.current_frame:04d}.png'
        self.rendering = True

    def post(self, scene, *args):
        self.current_frame += 1
        bpy.context.scene.frame_set(self.current_frame)
        self.rendering = False
        self.done = self.current_frame > self.end_frame

    def cancel(self, context):
        self.done = True

    def clear(self, context):
        context.scene.render.filepath = self.path
        bpy.app.handlers.render_init.remove(self.pre)
        bpy.app.handlers.render_write.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)
        context.scene.frame_set(self.start_frame)

    def init(self, context):
        # Get the start, end and current frame
        self.start_frame = bpy.context.scene.frame_start
        self.end_frame = bpy.context.scene.frame_end
        self.current_frame = bpy.context.scene.frame_start
        self.path = bpy.context.scene.render.filepath
        self.output_dir = '/animation/'
        os.makedirs(self.path + self.output_dir, exist_ok=True)
        self.done = False
        self.rendering = False
        bpy.app.handlers.render_init.append(self.pre)
        bpy.app.handlers.render_write.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        if context.object.type == 'CAMERA':
            context.scene.camera = context.object
        self.init(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.done:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            self.clear(context)
            return {'FINISHED'}
        if event.type == 'TIMER':
            if not self.rendering:
                bpy.ops.render.render("EXEC_DEFAULT", write_still=True)
        elif event.type == 'ESC':
            self.cancel(context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.init(context)
        while not self.done:
            bpy.ops.render.render("EXEC_DEFAULT", write_still=True)
        self.clear(context)

        return {'FINISHED'}

    
class LightFieldRender(bpy.types.Operator):
    bl_idname = "render.lightfield_render"
    bl_label = "Light Field Render"

    # path = bpy.props.StringProperty(default='')

    def write_meta(self, context):
        lf = context.scene.camera.lightfield
        with open(os.path.join(self.path, 'param.txt'), 'w') as f:
            f.write(f'camera: {context.scene.camera.name}\n')
            f.write(f'num_x: {lf.num_cols}\n')
            f.write(f'num_y: {lf.num_rows}\n')
            f.write(f'base_x: {lf.base_x}\n')
            f.write(f'base_y: {lf.base_y}\n')

    def pre(self, scene, *args):
        print(f'render on {self.progress:03d}/{len(self.poses):03d}')
        s, t = self.poses.idx2pos(self.progress)
        save_path = os.path.join(self.path, f'{s:02}_{t:02}')
        scene.render.filepath = save_path
        scene.camera.location = self.poses[self.progress]
        print(f'camera location: {scene.camera.location}')
        # scene.camera.data.shift_x = self.poses.get_shiftx(self.progress)
        # scene.camera.data.shift_y = self.poses.get_shifty(self.progress)
        self.rendering = True

    def post(self, scene, *args):
        self.progress += 1
        self.rendering = False
        self.done = self.progress >= len(self.poses)

    def init(self, context):
        self.done = False
        self.rendering = False
        self.poses = util.CamPoses(context.scene.camera)
        self.progress = 0
        self.path = context.scene.render.filepath
        bpy.app.handlers.render_init.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def cancel(self, context):
        self.done = True

    def clear(self, context):
        context.scene.render.filepath = self.path
        bpy.app.handlers.render_init.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)
        # context.scene.camera.data.shift_x = 0
        # context.scene.camera.data.shift_y = 0
        context.scene.camera.location = self.poses.pos

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        if context.object.type == 'CAMERA':
            context.scene.camera = context.object
        self.init(context)
        self.write_meta(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.done:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            self.clear(context)
            return {'FINISHED'}
        if event.type == 'TIMER':
            if not self.rendering:
                bpy.ops.render.render(
                    "EXEC_DEFAULT",
                    write_still=True, use_viewport=False)
        elif event.type == 'ESC':
            self.cancel(context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.init(context)
        self.write_meta(context)
        while not self.done:
            bpy.ops.render.render("EXEC_DEFAULT", write_still=True, use_viewport=False)
        self.clear(context)

        return {'FINISHED'}
    

class EventRender(bpy.types.Operator):
    bl_idname = "render.event_render"
    bl_label = "Event Render"

    def event_simulation(self, new_frame):
        new_frame = 0.299 * new_frame[:, :, 0] + 0.587 * new_frame[:, :, 1] + 0.114 * new_frame[:, :, 2]
        new_frame = util.lin_log(new_frame)
        if self.current_frame == self.start_frame:
            self.buffer = new_frame
        else:
            diff = new_frame - self.buffer
            mask = np.abs(diff) > self.threshold
            self.buffer[mask] = new_frame[mask]
            self.event_buffer[:, :, self.current_frame-2] = np.where(mask, np.sign(diff), 0)

    def pre(self, scene, *args):
        # print(f'render on frame {self.current_frame:04d}')
        self.rendering = True

    def post(self, scene, *args):
        # Update the buffer
        pixels = bpy.data.images['Viewer Node'].pixels
        pixels = np.array(pixels[:])
        pixels = pixels.reshape((self.res_y, self.res_x, 4))
        self.event_simulation(pixels)
        # DEBUG: Save npy
        # bpy.data.images['Render Result'].save_render(f'/tmp/event/frame_{self.current_frame:04d}.png')
        # np.save(f'/tmp/event/frame_{self.current_frame:04d}.npy', pixels)
        self.current_frame += 1
        bpy.context.scene.frame_set(self.current_frame)
        self.rendering = False
        self.done = self.current_frame > self.end_frame

    def cancel(self, context):
        self.done = True

    def clear(self, context):
        np.save(os.path.join(self.path, 'event_buffer.npy'), self.event_buffer)
        bpy.app.handlers.render_init.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)
        context.scene.frame_set(self.start_frame)

    def init(self, context):
        # Get the start, end and current frame
        self.start_frame = bpy.context.scene.frame_start
        self.end_frame = bpy.context.scene.frame_end
        self.current_frame = bpy.context.scene.frame_start
        self.done = False
        self.rendering = False
        # Get render resolution
        res = bpy.context.scene.render.resolution_percentage / 100
        self.res_x = int(bpy.context.scene.render.resolution_x * res)
        self.res_y = int(bpy.context.scene.render.resolution_y * res)
        self.buffer = np.zeros((self.res_y, self.res_x, 1), dtype=np.float32)
        self.event_buffer = np.zeros((self.res_y, self.res_x, self.end_frame-self.start_frame), dtype=np.int8)
        self.threshold = context.scene.camera.lightfield.threshold
        self.path = bpy.context.scene.render.filepath
        bpy.app.handlers.render_init.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        if context.object.type == 'CAMERA':
            context.scene.camera = context.object
        self.init(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.done:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            self.clear(context)
            return {'FINISHED'}
        if event.type == 'TIMER':
            if not self.rendering:
                bpy.ops.render.render("EXEC_DEFAULT", write_still=False)
        elif event.type == 'ESC':
            self.cancel(context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.init(context)
        while not self.done:
            bpy.ops.render.render("EXEC_DEFAULT", write_still=False)
        self.clear(context)

        return {'FINISHED'}
    

class EventLightFieldRender(bpy.types.Operator):
    bl_idname = "render.event_lightfield_render"
    bl_label = "Event Light Field Render"

    def write_meta(self, context):
        lf = context.scene.camera.lightfield
        with open(os.path.join(self.path, 'param.txt'), 'w') as f:
            f.write(f'camera: {context.scene.camera.name}\n')
            f.write(f'num_x: {lf.num_cols}\n')
            f.write(f'num_y: {lf.num_rows}\n')
            f.write(f'base_x: {lf.base_x}\n')
            f.write(f'base_y: {lf.base_y}\n')
            f.write(f'threshold: {lf.threshold}\n')
                    
    def event_simulation(self, new_frame):
        s, t = self.poses.idx2pos(self.lightfield_progress)
        new_frame = 0.299 * new_frame[:, :, 0] + 0.587 * new_frame[:, :, 1] + 0.114 * new_frame[:, :, 2]
        new_frame = util.lin_log(new_frame)

        header = f'{self.res_x} {self.res_y}'
        folder_path = os.path.join(self.path, f'pose_{s}_{t}')

        if self.current_frame == self.start_frame:
            self.buffer[:, :, s, t] = new_frame
            with open(os.path.join(folder_path, f'pose_{s}_{t}.txt'), 'w') as f:
                f.write(header + '\n')
        else:
            diff = new_frame - self.buffer[:, :, s, t]
            mask = np.abs(diff) > self.threshold
            self.buffer[:, :, s, t][mask] = new_frame[mask]
            # self.event_buffer[:, :, self.current_frame-1-self.start_frame, s, t] = np.where(mask, np.sign(diff), 0)

            # write to txt file
            
            mask_indices = np.argwhere(mask)
            if mask_indices.size > 0:
                # print(f'frame {self.current_frame:04d} frame_rate {self.frame_rate}')
                time_stamps = np.full(mask_indices.shape[0], self.current_frame / self.frame_rate)
                polarities = np.sign(diff[mask])
                event_data = np.column_stack((time_stamps, mask_indices[:, 1], self.res_y-mask_indices[:, 0], polarities))

                with open(os.path.join(folder_path, f'pose_{s}_{t}.txt'), 'a') as f:
                    np.savetxt(f, event_data, fmt='%.6f %d %d %d', comments='')



    def pre(self, scene, *args):
        s, t = self.poses.idx2pos(self.lightfield_progress)
        # scene.camera.data.shift_x = self.poses.get_shiftx(self.lightfield_progress)
        # scene.camera.data.shift_y = self.poses.get_shifty(self.lightfield_progress)
        scene.camera.location = self.poses[self.lightfield_progress]
        self.rendering = True

    def post(self, scene, *args):
        # Save the png file 
        s, t = self.poses.idx2pos(self.lightfield_progress)
        folder_path = os.path.join(self.path, f'pose_{s}_{t}')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        bpy.data.images['Render Result'].save_render(os.path.join(folder_path, f'{self.current_frame:04d}.png'))

        # Update the buffer
        pixels = bpy.data.images['Viewer Node'].pixels
        pixels = np.array(pixels[:])
        pixels = pixels.reshape((self.res_y, self.res_x, 4))
        self.event_simulation(pixels)

        self.lightfield_progress += 1
        self.lightfield_done = self.lightfield_progress >= len(self.poses)
        if self.lightfield_done:
            # print(f'render frame {self.current_frame:04d} done')
            self.lightfield_progress = 0
            # scene.camera.data.shift_x = 0
            # scene.camera.data.shift_y = 0
            self.current_frame += 1
            bpy.context.scene.frame_set(self.current_frame)
        
        self.rendering = False
        self.done = self.current_frame > self.end_frame

    def cancel(self, context):
        print('cancel')
        self.done = True

    def clear(self, context):
        # np.save(os.path.join(self.path, 'event_buffer_lightfield.npy'), self.event_buffer)
        context.scene.frame_set(self.start_frame)
        # context.scene.camera.data.shift_x = 0
        # context.scene.camera.data.shift_y = 0
        context.scene.camera.location = self.poses.pos
        bpy.app.handlers.render_init.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)

    def init(self, context):
        lf = context.scene.camera.lightfield
        # Camera poses (Light Field)
        self.path = bpy.context.scene.render.filepath
        self.poses = util.CamPoses(context.scene.camera)
        self.lightfield_progress = 0
        self.lightfield_done = False
        # Get the start, end and current frame
        self.start_frame = bpy.context.scene.frame_start
        self.end_frame = bpy.context.scene.frame_end
        self.current_frame = bpy.context.scene.frame_start
        self.done = False
        self.rendering = False
        self.frame_rate = bpy.context.scene.render.fps
        # Get render resolution
        res = bpy.context.scene.render.resolution_percentage / 100
        self.res_x = int(bpy.context.scene.render.resolution_x * res)
        self.res_y = int(bpy.context.scene.render.resolution_y * res)
        self.buffer = np.zeros((self.res_y, self.res_x, lf.num_rows, lf.num_cols), dtype=np.float32)
        # self.event_buffer = np.zeros((self.res_y, self.res_x, self.end_frame-self.start_frame, lf.num_rows, lf.num_cols), dtype=np.int8)
        self.threshold = context.scene.camera.lightfield.threshold
        
        # Bind handlers to the pipeline
        bpy.app.handlers.render_init.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        if context.object.type == 'CAMERA':
            context.scene.camera = context.object
        self.init(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.done:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            self.clear(context)
            return {'FINISHED'}
        if event.type == 'TIMER':
            if not self.rendering:
                bpy.ops.render.render("EXEC_DEFAULT", write_still=False, use_viewport=False)
        elif event.type == 'ESC':
            self.cancel(context)

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.init(context)
        while not self.done:
            bpy.ops.render.render("EXEC_DEFAULT", write_still=False, use_viewport=False)
        self.clear(context)

        return {'FINISHED'}
    

class EventGalvoRender(bpy.types.Operator):
    bl_idname = "render.event_galvo_render"
    bl_label = "Event Galvo Render"

    def event_simulation(self, new_frame):
        new_frame = 0.299 * new_frame[:, :, 0] + 0.587 * new_frame[:, :, 1] + 0.114 * new_frame[:, :, 2]
        new_frame = util.lin_log(new_frame)
        
        header = f'{self.res_x} {self.res_y}'
        folder_path = os.path.join(self.path, 'event_galvo')
        
        if self.current_frame == self.start_frame:
            self.buffer = new_frame
            with open(os.path.join(folder_path, f'event_galvo.txt'), 'w') as f:
                f.write(header + '\n')
        else:
            diff = new_frame - self.buffer
            mask = np.abs(diff) > self.threshold
            self.buffer[mask] = new_frame[mask]
            # self.event_buffer[:, :, self.current_frame-1-self.start_frame] = np.where(mask, np.sign(diff), 0)

            mask_indices = np.argwhere(mask)
            if mask_indices.size > 0:
                # print(f'frame {self.current_frame:04d} frame_rate {self.frame_rate}')
                time_stamps = np.full(mask_indices.shape[0], self.current_frame / self.frame_rate)
                polarities = np.sign(diff[mask])
                event_data = np.column_stack((time_stamps, mask_indices[:, 1], self.res_y-mask_indices[:, 0], polarities))

                with open(os.path.join(folder_path, f'event_galvo.txt'), 'a') as f:
                    np.savetxt(f, event_data, fmt='%.6f %d %d %d', comments='')

    def pre(self, scene, *args):
        # print(f'render on frame {self.current_frame:04d}')
        # Change the camera location on a circle
        frequency = scene.camera.lightfield.frequency
        angle = 2 * np.pi * (self.current_frame - self.start_frame) / frequency
        x = np.cos(angle)
        y = np.sin(angle)
        scene.camera.location = self.poses.get_galvo_position(x, y)

        # target = bpy.data.objects['Empty']
        # look_at = (target.location - scene.camera.location).normalized()
        # up = Vector((0, 0, 1))
        # right = look_at.cross(up).normalized()
        # up = right.cross(look_at).normalized()
        # rot_matrix = Matrix((
        #     right,
        #     up,
        #     -look_at
        # )).transposed()

        # scene.camera.rotation_euler = rot_matrix.to_euler()
        self.rendering = True

    def post(self, scene, *args):
        # Save the png file
        folder_path = os.path.join(self.path, f'event_galvo')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        bpy.data.images['Render Result'].save_render(os.path.join(folder_path, f'{self.current_frame:04d}.png'))

        # Update the buffer
        pixels = bpy.data.images['Viewer Node'].pixels
        pixels = np.array(pixels[:])
        pixels = pixels.reshape((self.res_y, self.res_x, 4))
        self.event_simulation(pixels)

        self.current_frame += 1
        bpy.context.scene.frame_set(self.current_frame)
        self.rendering = False
        self.done = self.current_frame > self.end_frame

    def cancel(self, context):
        self.done = True

    def clear(self, context):
        # np.save(os.path.join(self.path, 'event_buffer.npy'), self.event_buffer)
        bpy.app.handlers.render_init.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.clear)
        context.scene.frame_set(self.start_frame)

    def init(self, context):
        # Get the start, end and current frame
        self.poses = util.CamPoses(context.scene.camera)
        self.start_frame = bpy.context.scene.frame_start
        self.end_frame = bpy.context.scene.frame_end
        self.current_frame = bpy.context.scene.frame_start
        self.done = False
        self.rendering = False
        self.frame_rate = bpy.context.scene.render.fps
        # Get render resolution
        res = bpy.context.scene.render.resolution_percentage / 100
        self.res_x = int(bpy.context.scene.render.resolution_x * res)
        self.res_y = int(bpy.context.scene.render.resolution_y * res)
        self.buffer = np.zeros((self.res_y, self.res_x, 1), dtype=np.float32)
        # self.event_buffer = np.zeros((self.res_y, self.res_x, self.end_frame-self.start_frame), dtype=np.int8)
        self.threshold = context.scene.camera.lightfield.threshold
        self.path = bpy.context.scene.render.filepath
        bpy.app.handlers.render_init.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.clear)

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        self.timer = context.window_manager.event_timer_add(
            0.5, window=context.window)
        if context.object.type == 'CAMERA':
            context.scene.camera = context.object
        self.init(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.done:
            context.window_manager.event_timer_remove(self.timer)
            self.timer = None
            self.clear(context)
            return {'FINISHED'}
        if event.type == 'TIMER':
            if not self.rendering:
                bpy.ops.render.render("EXEC_DEFAULT", write_still=False)
        elif event.type == 'ESC':
            self.cancel(context)

        return {'PASS_THROUGH'}