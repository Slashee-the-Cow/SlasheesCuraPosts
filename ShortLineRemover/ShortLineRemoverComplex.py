# Short Line Remover
# Written by Slashee the Cow, replicating a function created be Jhaonor.

import math

from ..Script import Script
from UM.Application import Application

class ShortLineRemover(Script):

    # Constants for acting on different kinds of lines
    LINE_NOT_MOVE = "LINE_NOT_MOVE"
    LINE_MOVE = "LINE_MOVE"
    LINE_Z_MOVE = "LINE_Z_MOVE"  # We pay special attention to Z moves.
    LINE_EXTRUSION = "LINE_EXTRUSION"
    LINE_COMMENT = "LINE_COMMENT"
    LINE_NONMESH = "LINE_NONMESH"
    LINE_RETRACT = "LINE_RETRACT"
    
    def __init__(self):
        super().__init__()

    # The odds of encountering the arc moves are low, but I prefer to be thorough
    move_commands = ("G0", "G1", "G2", "G3")

    def get_2d_coords(self, line: str, prev_coords = None) -> tuple[float, float]:
        """Safely grab 2D (X and Y) coordinates from a gcode line
        with fallback defaults, or previous coordinates."""
        return self.getValue(line, "X", prev_coords[0] if prev_coords else 0,
                self.getValue(line, "Y", prev_coords[1] if prev_coords else 0))

    def is_non_extrusion_move(self, line) -> bool:
        """Convenience function to see if a line is a move without extrusion."""
        return line.startswith(self.move_commands) and "E" not in line and ("X" in line or "Y" in line)

    def is_extrusion_move(self, line) -> bool:
        """Convenience function to see if a line is a move with an extrusion."""
        return line.startswith(self.move_commands) and "E" in line and ("X" in line or "Y" in line)

    def is_move(self, line: str) -> bool:
        """These convenience functions are getting out of control.
        Shortcut for is_non_extrusion_move() or is_extrusion_move()"""
        return self.is_non_extrusion_move(line) or self.is_extrusion_move(line)

    def is_next_line_extrusion_move(self, layer: list[str], line_index: int,
                                    current_coords: tuple[float, float] = None) -> tuple[bool, float]:
        """Grabs whether the next line is an extrusion move and its length.
        Returns True, math.inf if last line in layer to guarantee end.
        Returns False, -1 if not an extrusion move.
        Returns True, -1 if not passed current_coords so can't measure distance."""
        if line_index == len(layer) - 1:
            return True, math.inf
        if self.is_non_extrusion_move(layer[line_index + 1]):
            return False, -1
        if self.is_extrusion_move(layer[line_index + 1]):
            if current_coords:
                return True, math.dist(current_coords,
                                   self.get_2d_coords(layer[line_index + 1], current_coords))
            return True, -1
        return False, -1

    def get_next_extrusion_length(self, layer: list[str], line_index: int, current_coords: tuple[float, float] = None) -> tuple[float, int]:
        """Searches ahead the current layer for extrusion commands and gets the length and index.
        Returns -1, -1 if one can't be found."""
        last_coords = current_coords if current_coords else (-1,-1)
        for i in range(line_index, len(layer)):
            line = layer[i]
            if self.is_non_extrusion_move(line):
                last_coords = self.get_2d_coords(line, last_coords)
            if self.get_line_type(line) == self.LINE_NONMESH:
                # Equivalent enough to hitting the end
                return -1, -1
            if self.is_extrusion_move(line):
                return math.dist(last_coords, self.get_2d_coords(line, last_coords)), i
        # In theory we should hit the ;NONMESH before we get here. But can't hurt to be sure.
        return -1, -1
            
    def get_line_type(self, line: str) -> str:
        """Returns one of the constants above depending on what sort of line it is"""
        if ";NONMESH" in line:
            return self.LINE_NONMESH  # End of a layer
        if (self.is_move(line)
            and self.getValue(line, "E")
            and not self.getValue("X")
            and not self.getValue("Y")
            and not self.getValue("Z")):
            return self.LINE_RETRACT
        if self.is_move(line) and self.getValue(line, "Z") \
            and not self.getValue("X") and not self.getValue("Y"):
            return self.LINE_Z_MOVE
        if self.is_extrusion_move(line):
            return self.LINE_EXTRUSION
        if self.is_non_extrusion_move(line):
            return self.LINE_MOVE
        if line.lstrip().startswith(";"):
            return self.LINE_COMMENT
        return self.LINE_NOT_MOVE

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
        max_delete_length: float = self.getSettingValueByKey("max_length")

        global_stack = Application.getInstance().getGlobalContainerStack()
        z_hop_height: float = float(global_stack.getProperty("retraction_hop", "value"))  # Actually used in calculations, so string won't cut it.
        z_hop_speed: str = str(float(global_stack.getProperty("speed_z_hop", "value")) * 60)  # Convert Cura's mm/s to Marlin mm/min

        z_hop_command = "G1"  # Cura seems to use G1 F<speed> Zxx for Z hops

        def is_z_hop(line: str, height: float, command: str = z_hop_command, speed: str = z_hop_speed):
            if isinstance(self.getValue(line,"Z"), float):
                return False  # This should probably never happen.
            if line.getValue("F"):
                return (line.startswith(command)
                    and self.getValue(line, "F") == speed
                    and math.isclose((self.getValue(line, "Z")), height)
                    and "X" not in line and "Y" not in line)
            return False

        total_extrusion_distance: float = 0.0

        prev_coords: tuple[float, float] = None
        in_z_hop_section: bool = False
        last_e: float = 0.0
        last_z: float = 0.0
        unhop_z: float = 0.0

        for layer_index, layer in enumerate(data):
            total_extrusion_distance = 0.0
            prev_coords = None
            in_z_hop_section = False
            new_lines: list[str] = []
            section_lines_all: list[str] = []
            section_lines_remove: list[str] = []
            layer_lines = layer.splitlines()
            
            for line_index, line in enumerate(layer_lines):
                if line_index == len(layer_lines - 1):
                    # We should probably never be in a Z-hop section at the end of a layer.
                    # But if we are, we want all those lines.
                    if in_z_hop_section:
                        new_lines.extend(section_lines_all)
                        break
                
                match self.get_line_type(line):
                    case self.LINE_NONMESH:
                        if in_z_hop_section:
                            if total_extrusion_distance < max_delete_length:
                                new_lines.extend(section_lines_remove)
                                new_lines.append(f"G92 E{last_e}")
                            else:
                                new_lines.extend(section_lines_all)
                            section_lines_all = []
                            section_lines_remove = []
                            total_extrusion_distance = 0.0
                            in_z_hop_section = False
                            unhop_z = 0.0
                        new_lines.append(line)
                    case self.LINE_Z_MOVE:
                        if in_z_hop_section:
                            if is_z_hop(line, last_z + z_hop_height):
                                if self.get_next_extrusion_length(layer, line_index, prev_coords)[0] > max_delete_length:
                                    # Next extrusion is long enough. Drop us out of warp!
                                    if total_extrusion_distance < max_delete_length:
                                        new_lines.extend(section_lines_remove)
                                        new_lines.append(f"G92 E{last_e}")
                                    else:
                                        new_lines.extend(section_lines_all)
                                    in_z_hop_section = False
                                    section_lines_all = []
                                    section_lines_remove = []
                                    total_extrusion_distance = 0.0
                                    unhop_z = 0.0
                                    # We're not actually recording this emergency exit.
                                    continue
                            else:
                                # We only really care about going up 1x Z hop, but we need to track this
                                last_z = self.getValue("Z")
                                section_lines_all.append(line)
                        else:
                            if is_z_hop(line, last_z + z_hop_height):
                                unhop_z = last_z
                                in_z_hop_section = True
                                new_lines.append(line)  # Going up initially always gets recorded.
                            else:
                                # We're not in Z hop section (or starting one), just add it to the list.
                                new_lines.append(line)
                    case self.LINE_MOVE:
                        prev_coords = self.get_2d_coords(line, prev_coords)
                        if in_z_hop_section:
                            section_lines_all.append(line)
                        else:
                            new_lines.append(line)
                        if self.getValue("Z"):
                            last_z = self.getValue("Z")
                            
                    case self.LINE_EXTRUSION:
                        last_e = self.getValue(line, "E")
                        if in_z_hop_section:
                            total_extrusion_distance += math.dist(prev_coords, self.get_2d_coords(line, prev_coords))
                            section_lines_all.append(line)
                        else:
                            new_lines.append(line)
                        prev_coords = self.get_2d_coords(line, prev_coords)
                        if self.getValue("Z"):
                            last_z = self.getValue("Z")
                    case _:  # I know I'm checking for more different kinds of lines above. But at this point I don't think it matters.
                        if in_z_hop_section:
                            section_lines_all.append(line)
                            section_lines_remove.append(line)
                        else:
                            new_lines.append(line)

                data[layer_index] = "\n".join(new_lines) + "\n"

        return data

