import bpy
import sys

def launch(addons_to_load, options):
    if bpy.app.version < (2, 80, 34):
        handle_fatal_error("Please use a newer version of Blender")

    from . import installation
    installation.ensure_packages_are_installed(["debugpy", "requests", "pillow"])

    from . import load_addons
    load_addons.setup_addon_links(addons_to_load)

    load_addons.load(addons_to_load, options)

def handle_fatal_error(message):
    print()
    print("#"*80)
    for line in message.splitlines():
        print("> ERROR: ", line)
    print("#"*80)
    print()
    sys.exit(1)
