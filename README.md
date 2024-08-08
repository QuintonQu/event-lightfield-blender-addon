# Event - Light Field Rendering Blender Plugin

This is a blender plugin to help you synthesize render light field. In effect, you are allowed to render a grid of camera positions. 
This is a blender plugin to help you simulate the event camera (brute force) with light field. In effect, you are allowed to render events from a grid of camera positions.

## Installation

- Download the repository as a zip file and install it in Blender as a zip file.
- Enable the plugin in Blender.
- You can find the plugin in the Camera tab.

## Usage

Make an animation and render it with the plugin. The plugin will render the event - light field for you.
You can set grid size, numbers, and event threshold in the plugin.
Set resolution and path using the original blender settings blocks.

### Warning

Make sure to add "RGB to BW" node in the compositor to convert the rendered image to grayscale.
Make sure to add "Viewer" node in the compositor to give plugin the ability to get the rendered data.

## License
This is a modified version of the Blender-addon-light-field-camera plugin. The original plugin is licensed under the terms of the GNU General Public License. The original plugin can be found [here](https://github.com/gfxdisp/Blender-addon-light-field-camera).