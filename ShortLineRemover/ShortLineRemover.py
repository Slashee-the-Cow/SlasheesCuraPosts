# Short Line Remover
# Written by Slashee the Cow, replicating a function created be Jhaonor.

import math

from ..Script import Script
from UM.Application import Application

class ShortLineRemover(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Short Line Remover",
            "key": "ShortLineRemover",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "max_length":
                {
                    "label": "Maximum deletion length",
                    "description": "The maximum section length to be deleted",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 1,
                    "minimum_value": 0.1,
                    "maximum_value_warning": 5
                }
            }
        }"""

    def is_there_another_g0(self, remaining_layer: list[str]) -> bool:
        for line in remaining_layer:
            if line.startswith("G0"):
                return True
        return False
    
    def execute(self, data):
        max_delete_length: float = float(self.getSettingValueByKey("max_length"))
        previous_coords: tuple[float, float, float] = (None, None, None)

        def update_previous_coords(line, prev_coords = previous_coords):
            new_x = self.getValue(line, "X")
            new_y = self.getValue(line, "Y")
            new_z = self.getValue(line, "Z")
            return \
                (new_x if new_x is not None else prev_coords[0],
                new_y if new_y is not None else prev_coords[1],
                new_z if new_z is not None else prev_coords[2])

        remove_section: bool = False
        section_keep: list[str] = []
        section_remove: list[str] = []
        section_length: float = 0.0
        start_z: float = None
        last_z: float = None
        z_moved_down: bool = None
        
        for layer_index, layer in enumerate(data):
            if layer_index == len(data) - 1:
                # This is end gcode - we're done.
                break
            new_lines: list[str] = []
            layer_lines = layer.splitlines()
            layer_finished = False  # Make sure to include everything after the last G0
            
            for line_index, line in enumerate(layer_lines):
                if layer_finished:
                    new_lines.append(line)
                    continue

                if line.startswith("G0"):
                    # Sections end on travel moves
                    if remove_section:
                        # This sections's gotta go
                        new_lines.extend(section_remove)
                    else:
                        new_lines.extend(section_keep)
                    remove_section = False
                    section_keep.clear()
                    section_remove.clear()
                    section_length = 0.0

                # Start a section on a G0 with Z
                if line.startswith("G0") and "Z" in line:
                    section_keep.append(line)
                    previous_coords = update_previous_coords(line, previous_coords)
                    start_z = previous_coords[2]
                    section_length = 0.0
                    z_moved_down = False
                    last_z = None

                # Care about a G1 only if it's had a G0 with Z before it
                elif line.startswith("G1") and len(section_keep) > 0:
                    coords = (self.getValue(line, "X"), self.getValue(line, "Y"), self.getValue(line, "Z"))
                    if coords[0] is not None and coords[1] is not None:
                        if previous_coords[0] is not None and \
                            previous_coords[1] is not None:
                            section_length += math.dist(previous_coords, coords)
                        previous_coords = update_previous_coords(line, previous_coords)
                    if coords[2] is not None:
                        if start_z is not None and coords[2] < start_z:
                            z_moved_down = True
                        last_z = coords[2]
                    section_keep.append(line)

                else:
                    # Other lines get kept regardless
                    if len(section_keep) > 0:
                        section_remove.append(line)
                        section_keep.append(line)
                    else:
                        new_lines.append(line)

                # Check to see if we're about to hit a movement or end of layer and end things
                final_g0 = False
                if line_index + 1 < len(layer_lines) \
                    and layer_lines[line_index + 1].startswith("G0"):
                    if line_index + 2 < len(layer_lines):
                        final_g0 = self.is_there_another_g0(layer_lines[line_index + 2:])
                        if not final_g0:
                            remove_section = section_length < max_delete_length
                    else:  # End of the layer
                        final_g0 = True

                if not final_g0:
                    # Do a proper check to see if we've gone down
                    if z_moved_down and start_z is not None \
                        and last_z is not None and last_z == start_z \
                        and section_length < max_delete_length:
                        remove_section = True
                    
                if final_g0 or line_index == len(layer_lines) - 1:
                    remove_section = section_length < max_delete_length
                    layer_finished = True
                    if True:
                        new_lines.extend(section_remove)
                        section_remove.clear()
                        section_keep.clear()
                        section_length = 0.0
                        remove_section = False
                    else:
                        new_lines.extend(section_keep)
            data[layer_index] = "\n".join(new_lines) + "\n"
        return data
