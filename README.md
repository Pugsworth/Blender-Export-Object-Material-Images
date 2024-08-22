# Blender-Export-Object-Material-Images
Exports the images used in the materials of an object.


# To Do
- [/] Error handling
- [ ] Work off of all the selected objects, not just the active one!
- [ ] Fix all paths to use pathlib types or something
- [ ] Determine how to setup add-on for legacy and modern (4.2.0) Blender.
      Modern (4.2.0) Blender uses the blender_manifest.toml system.
      I know this would also work as far back as (4.0.0).
      Because of this, I included the bl_info metadata dictionary still.
      I need to do some testing to determine if including both would still allow the add-on to be installed on both
      versions and if the information is pulled from the correct place.
