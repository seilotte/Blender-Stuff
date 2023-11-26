#https://blender.stackexchange.com/questions/274712/how-to-channel-pack-texture-in-python

import bpy
import numpy

def pack_image_channels(pack_order, directory):
    dst_array = None
    has_alpha = False

    # Build the packed pixel array
    for pack_item in pack_order:
        image = pack_item[0]

        # Initialize arrays on the first iteration
        if dst_array is None:
            w, h = image.size
            src_array = numpy.empty(w * h * 4, dtype=numpy.float32)
            dst_array = numpy.ones(w * h * 4, dtype=numpy.float32)

        assert image.size[:] == (w, h), "Images must be same size"

        # Fetch pixels from the source image and copy channels
        image.pixels.foreach_get(src_array)
        for src_chan, dst_chan in pack_item[1:]:
            if dst_chan == 3:
                has_alpha = True
            dst_array[dst_chan::4] = src_array[src_chan::4]

    # Create image from the packed pixels
    dst_image = bpy.data.images.new("Packed Image", w, h, alpha=has_alpha)
    dst_image.pixels.foreach_set(dst_array)

    # Since the image doesn't exist on disk, we need to pack it into the .blend
    # or it won't exist after the .blend is closed
#    dst_image.pack()

    # Save image to directory.
    dst_image.filepath_raw = directory
    dst_image.file_format = 'PNG'
    dst_image.save()

    return dst_image


pack_order = [
    # 0 = Red, 1 = Green, 2 = Blue, 3 = Alpha.
    (bpy.data.images['base_col.png'], (0, 0), (1, 1), (2, 2)),
    (bpy.data.images['ANL_base.png'], (3, 3))
]

file_name = f'Packed_Image.png' # Careful! It will replace the image if it matches the name.
directory = "//" + file_name # Replace "//" with your directory.

pack_image_channels(pack_order, directory)