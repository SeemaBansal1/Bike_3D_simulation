"""Export the "Bike" collection of bike.blend to GLB for the website.

Usage (from this folder):
    blender -b bike.blend --python export.py

Writes:
    assets/bike.glb        uncompressed, always used as the fallback
    assets/bike-draco.glb  Draco-compressed, loaded first by the site

Only objects in the "Bike" collection are exported (the "Studio" collection's
floor, walls, lights and camera are skipped). The scene is set to the last frame
of the timeline first, because that frame is the assembled pose; the keyframed
assemble animation itself is not exported.
"""
import os
import bpy

BLEND_DIR = bpy.path.abspath("//")
OUT_DIR = os.path.join(BLEND_DIR, "assets")
os.makedirs(OUT_DIR, exist_ok=True)

scene = bpy.context.scene
scene.frame_set(scene.frame_end)  # assembled pose

bike = bpy.data.collections.get("Bike")
if bike is None:
    raise SystemExit("No collection named 'Bike' in this file")

view_layer = bpy.context.view_layer
for obj in view_layer.objects:
    obj.select_set(False)

bike_objects = list(bike.all_objects)  # snapshot: visibility edits invalidate the live iterator
selected = 0
for obj in bike_objects:
    if obj.name not in view_layer.objects:
        continue
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.hide_select = False
    obj.select_set(True)
    selected += 1
view_layer.objects.active = bike_objects[0]
print(f"[export] selected {selected} objects from 'Bike'")

common = dict(
    export_format="GLB",
    use_selection=True,
    export_yup=True,
    export_apply=True,        # bevel / solidify modifiers
    export_extras=True,       # group, exploded_off, side -> node.extras
    export_cameras=False,
    export_lights=False,
    export_animations=False,  # ignore the keyframed assemble animation
    export_current_frame=True,  # without this the exporter samples frame 0 (exploded pose)
    export_attributes=False,  # the web shader recomputes 'apos' itself
    export_materials="EXPORT",
    export_image_format="AUTO",
)

plain = os.path.join(OUT_DIR, "bike.glb")
bpy.ops.export_scene.gltf(filepath=plain, export_draco_mesh_compression_enable=False, **common)
print(f"[export] wrote {plain} ({os.path.getsize(plain) / 1e6:.2f} MB)")

draco = os.path.join(OUT_DIR, "bike-draco.glb")
try:
    bpy.ops.export_scene.gltf(
        filepath=draco,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=16,
        export_draco_normal_quantization=12,
        export_draco_texcoord_quantization=12,
        **common,
    )
    print(f"[export] wrote {draco} ({os.path.getsize(draco) / 1e6:.2f} MB)")
except Exception as exc:  # Draco library missing from this Blender build
    print(f"[export] Draco export failed, site will use bike.glb only: {exc}")
