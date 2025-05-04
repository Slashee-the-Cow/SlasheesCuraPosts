# Short Line Remover
# Written by Slashee the Cow, replicating a function created by Jhaonor.

import math

from ..Script import Script
from UM.Application import Application
from UM.Logger import Logger

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
    
    def execute(self, data):

        max_delete_length: float = float(self.getSettingValueByKey("max_length"))
        previous_coords: tuple[float, float, float] = (None, None, None)
        
        def update_previous_coords(line: str, prev_coords: tuple[float, float, float] = previous_coords) -> tuple[float, float, float]:
            new_x = self.getValue(line, "X")
            new_y = self.getValue(line, "Y")
            new_z = self.getValue(line, "Z")
            return \
                (new_x if new_x is not None else prev_coords[0],
                new_y if new_y is not None else prev_coords[1],
                new_z if new_z is not None else prev_coords[2])

        def parse_coords(line: str) -> tuple[float, float, float]:
            x = self.getValue(line, "X")
            y = self.getValue(line, "Y")
            z = self.getValue(line, "Z")
            return x, y, z

        remove_section: bool = False
        section_whole: list[str] = []
        section_nomoves: list[str] = []
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
            #Logger.log("d", f"layer_index: {layer_index}")
            
            for line_index, line in enumerate(layer_lines):
                #Logger.log("d", f"line_index: {line_index}, line: {line}")
                if layer_finished:
                    new_lines.append(line)
                    continue

                if line.startswith("G0"):
                    # Sections end on travel moves, figure out if it needs to be removed
                    if remove_section:
                        # This sections's gotta go
                        new_lines.extend(section_nomoves)
                    else:
                        new_lines.extend(section_whole)
                    remove_section = False
                    section_whole.clear()
                    section_nomoves.clear()
                    section_length = 0.0

                # Start a section on a G0 with Z
                if line.startswith("G0") and "Z" in line:
                    section_whole.append(line)
                    previous_coords = update_previous_coords(line, previous_coords)
                    start_z = previous_coords[2]
                    section_length = 0.0
                    z_moved_down = False
                    last_z = None

                # Care about a G1 only if it's had a G0 with Z before it
                elif line.startswith("G1") and section_whole:
                    coords = parse_coords(line)
                    if coords[0] is not None and coords[1] is not None:
                        if previous_coords and coords:
                            try:
                                section_length += math.dist(previous_coords[:2], coords[:2])
                            except TypeError:
                                Logger.log("w", f"Distance calculation failed on coords {coords} and previous_coords {previous_coords}")
                        previous_coords = update_previous_coords(line, previous_coords)
                    if coords[2] is not None:
                        if start_z is not None and coords[2] < start_z:
                            z_moved_down = True
                        last_z = coords[2]
                    section_whole.append(line)

                else:
                    # Other lines get kept regardless
                    if section_whole:
                        section_nomoves.append(line)
                        section_whole.append(line)
                    else:
                        new_lines.append(line)

                # Check to see if next line is G0 or end of layer
                if (line_index + 1 < len(layer_lines) and layer_lines[line_index + 1].startswith("G0")) \
                    or (line_index == len(layer_lines) - 1):
                    if start_z is not None and z_moved_down \
                        and last_z is not None and last_z == start_z \
                        and section_length < max_delete_length:
                        remove_section = True
            # Handle actually removing data at the end of the layer
            if remove_section:
                new_lines.extend(section_nomoves)
                layer_finished = True
            else:
                new_lines.extend(section_whole)
            remove_section = False
            section_whole.clear()
            section_nomoves.clear()
            section_length = 0.0

            data[layer_index] = "\n".join(new_lines) + "\n"
        return data
