# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "SeiTools",
    "author": "Seilotte",
    "version": (1, 3, 3),
    "blender": (3, 6, 0),
    "location": "View3D > Properties > Sei",
    "description": "Random collection of tools for my personal use.",
    "category": "3D View",
    "tracker_url": "https://github.com/seilotte/Blender-Stuff/tree/main/Add-ons/Sei_Tools"
}

import importlib

from . import sei_variables
from . import sei_ui

# Each module is expected to have a register() and unregister() fucntion.
modules = [
    sei_variables,
    sei_ui,
]

def register():
    for m in modules:
        importlib.reload(m)
        try:
            m.register()
        except:
            pass

def unregister():
    for m in modules:
        m.unregister()