bl_info = {
        "name": "Export Object Material Images",
        "description": "This operator allows for exporting ",
        "author": "Uriah",
        "version": (1, 0, 1),
        "blender": (4, 0, 0),
        "category": "Input-Export",
        "warning": "Alpha version - expect some errors!",
}



import os
from typing import Annotated
import bpy
import pathlib



def is_node_active(node, output_node):
    """Recursively checks if a node is connected to the output node"""
    if node == output_node:
        return True
    for output in node.outputs:
        for link in output.links:
            if is_node_active(link.to_node, output_node):
                return True
    return False


def image_format_to_file_extension(fmt: str) -> str:
    """Get the expected file extension from one of the built-in image formats."""
    match fmt:
        case "PNG":
            return "png"
        case "BMP":
            return "bmp"
        case "TARGA":
            return "tga"
        case "TARGA_RAW":
            return "tga"
        case "JPEG":
            return "jpg"
        case "JPEG2000":
            return "jp2"
        case "TIFF":
            return "tiff"
        case "WEBP":
            return "webp"
        case "HDR":
            return "hdr"
        case "OPEN_EXR":
            return "exr"
        case "IRIS":
            return "sgi"
        case _:
            return ""


def get_file_extension(path: str) -> str:
    """Returns the file extension from a string path."""
    ppath = pathlib.PurePath(path)
    ext = ppath.suffix
    return ext


def get_active_material_textures(obj) -> list[object]:
    """
        Fetches the materials of the object and iterates through for all "TEX_IMAGE" nodes.
        Then, tries to determine which of these nodes are actively used by recursively tracing back to the first "OUTPUT_MATERIAL" node found.

        Potential failure points:
        - If there are multiple "OUTPUT_MATERIAL" nodes (is this possible?).

        Cases where this doesn't work, but doesn't fail or results in unexpected outcomes:
        - Material isn't using nodes (who does this anymore?)
        - Material is made up of multiple textures nodes to procedurally create the material.
          This is expecting only complete texture nodes.
          This could be a major issue since there's no checking or safeties in place for it.
    """
    textures = []

    # Ensure an object is selected
    if obj and obj.type == 'MESH':
        # Loop through all materials on the object
        for mat_slot in obj.material_slots:
            mat = mat_slot.material
            if mat:
                # print(f"Material: {mat.name}")
                # Check if the material has a node tree (using nodes)
                if mat.use_nodes:
                    # Find the material output node
                    output_node = None
                    for node in mat.node_tree.nodes:
                        if node.type == 'OUTPUT_MATERIAL':
                            output_node = node
                            break

                    if output_node:
                        # Loop through all nodes in the material's node tree
                        for node in mat.node_tree.nodes:
                            # Check if the node is a texture node
                            if node.type == 'TEX_IMAGE':
                                texture = node.image
                                if texture:
                                    active = is_node_active(node, output_node)
                                    # status = "active" if active else "inactive"
                                    # print(f"  Texture: {texture.name} ({status})")
                                    if active:
                                        textures.append(texture);
    return textures


def save_images(context: bpy.types.Context, dest: str):
    """
        Saves the images used in the textures of the active object.
    """
    # Get the selected object
    obj = context.active_object
    if obj is None:
        raise Exception("No active object!")


    textures = get_active_material_textures(obj)
    if len(textures) == 0:
        raise Exception("Mesh has no textures!")

    # Gotta make a new temporary scene for setting the export parameters.
    # It's a very strange way of doing it, but it's apparently the only way to actually save an Image as a specific format without saving the original image to a new location.
    temp_scene = bpy.data.scenes.new("temp_export_scene")
    settings = temp_scene.render.image_settings
    settings.file_format = "PNG"
    settings.color_mode = "RGBA"
    settings.color_depth = '8'
    settings.compression = 15

    for tex in textures:
        is_packed = tex.packed_file is not None
        full_path = tex.filepath
        # print(f"Texture '{tex.name}' '{tex.file_format}' '{tex}' embedded: {is_packed} path is '{tex.filepath}'")

        # Extracting the correct file extension to use for the image, accounting for if the image name already included the extension.
        # Thanks pathlib!
        format_ext = image_format_to_file_extension(settings.file_format)
        # ext = get_file_extension(tex.name)
        save_path = pathlib.PurePath(dest, tex.name).with_suffix('.'+format_ext)
        # print(f"{save_path=}")
        try:
            tex.save_render(str(save_path), scene=temp_scene)
        except Exception as e:
            # TODO: Do something about this...
            pass

    bpy.data.scenes.remove(temp_scene)


#
# Now for the actual operator!
#

from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty
from bpy.types import Operator


class SaveObjectImagesOperator(Operator, ExportHelper):
    bl_idname = "export_test.save_object_images"
    bl_label = "Save object material images"

    filter_glob: StringProperty(
        default="*/*",
        options={"HIDDEN"},
        maxlen=255,
        ) # type: ignore

    filename_ext: StringProperty(
        default="",
        options={"HIDDEN"},
        maxlen=255,
    ) # type: ignore

    # NOTE: I'm not sure if this definition is even required.
    filename: StringProperty(
        default=""
    ) # type: ignore


    def invoke(self, context, event):
        # WEIRD: I have to explicitly set this here to avoid having it default to the name of the blend file.
        self.properties.filename = ""
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}
    # return super().invoke(context, event)

    def execute(self, context):
        userpath = self.properties.filepath
        if not os.path.isdir(userpath):
            self.report({"ERROR"}, f"Path '{userpath}' doesn't exist!")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Selected '{userpath}'")
        try:
            save_images(context, userpath)
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export images:\n{e}")
            return {"CANCELLED"}


def menu_func_export(self, context):
    self.layout.operator(SaveObjectImagesOperator.bl_idname, text="Save Object Images Operator")


def register():
    # Register the Operator
    bpy.utils.register_class(SaveObjectImagesOperator)
    # Register in the File>Export menu
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    # Register in the View3D Object space
    bpy.types.VIEW3D_MT_object.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(SaveObjectImagesOperator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.VIEW3D_MT_object.remove(menu_func_export)


if __name__ == "__main__":
    # Oof, this one's a doozy! This is some wild shit!
    # Through looking at the source code and some poking around in Python, I have determined the location of the 'menu_func_export' functions and how to remove them without the function pointer reference.
    #
    # Blender uses a base-class for creating the registration of these drawing functions.
    #   MenuClass.append(drawing_func)
    #   MenuClass.remove(drawing_func)
    # The menu class has a "draw" method that also calls similar drawing functions to create the default menus in Blender.
    #
    # Each menu class extends the  base class of "Menu" which extends "_GenericUI".
    # "_GenericUI" class is some kind of weird hack to allow for the entire system to be extensible.
    # First, it creates a "_draw_funcs" array attribute on the "draw" method.
    # Then, it overwrites the "draw" method with a new one that calls the original method in addition to iterating this "_draw_funcs" array and calling all of the contained functions.
    # When you want to add a new menu item, you append a function that calls all of the drawing functions you want.
    # For example, `layout.operator(...)` just draws a line of text that calls an operator when clicked.
    #
    # It's clever to abuse the hell out of the Python language in this way to create a method for extending the functionality of these menu classes, but it requires creating a bass class and extending it.
    # At this point, there's already the access to the original "Menu" class, so what's the point in this super-roundabout method for implementing this all??
    # My theory is a mix of open-source bad code shenanigans and backwards compatability.
    # bad_dfs = []
    # for df in getattr(bpy.types.TOPBAR_MT_file_export.draw, "_draw_funcs", None):
    #     code = getattr(df, "__code__")
    #     if code.co_names[2] == SaveObjectImagesOperator.__name__:
    #         bad_dfs.append(df)
    # for df in bad_dfs:
    #     bpy.types.TOPBAR_MT_file_export.remove(df)


    register()

    # Test call
    # bpy.ops.export_test.save_object_images("INVOKE_DEFAULT")

    # unregister()
