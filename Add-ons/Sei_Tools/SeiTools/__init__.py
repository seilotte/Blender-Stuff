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
    "version": (1, 3, 2),
    "blender": (3, 6, 0),
    "location": "View3D > Properties > UmU",
    "description": "Random collection of tools for my personal use.",
    "category": "3D View"
}
    
import importlib

#from . import sei_panel
from . import sei_custom_variables
from . import sei_ui_rig_tools
#from . import sei_ui_mesh_tools
from . import sei_ui_data_tools
from . import sei_ui_blender
from .sei_rig_tools import sei_ot_rig_tools
#from .sei_mesh_tools import sei_ot_mesh_tools
from .sei_data_tools import sei_ot_data_tools

# Each module is expected to have a register() and unregister() function.
modules = [
#    sei_panel,
    sei_custom_variables,
    sei_ui_rig_tools,
#    sei_ui_mesh_tools,
    sei_ui_data_tools,
    sei_ui_blender,
    sei_ot_rig_tools,
#    sei_ot_mesh_tools,
    sei_ot_data_tools,
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