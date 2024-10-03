# Support Entry/Exit Retract by Slashee the Cow
# Adds retractions when entering/leaving support if they're not already there.
#
# An audience request from Xhoax

# V1 Initial, inevitably buggy version
# V2 D'oh! Forgot to multiply the retraction for being in mm/min

from ..Script import Script
from UM.Application import Application

class SupportEntryExitRetract(Script):

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Support Entry/Exit Retract",
            "key": "SupportEntryExitRetract",
            "metadata": {},
            "version": 2,
            "settings": {}
        }"""

    def execute(self, data):
        CuraStack = Application.getInstance().getGlobalContainerStack()

        try:
            support_extruder_num = int(CuraStack.getProperty("support_extruder_nr", "value"))
            if support_extruder_num == -1:
                support_extruder_num = 0
        except Exception as e:
            support_extruder_num = 0
        support_extruder = CuraStack.extruderList[support_extruder_num]

        retract_distance = float(support_extruder.getProperty("retraction_amount", "value"))
        retract_speed = int(support_extruder.getProperty("retraction_speed", "value")) * 60

        last_move_retraction = False
        in_support_section = False

        previous_e = 0.0
        current_e = 0.0

        last_extrusion_move_layer = 0
        last_extrusion_move_index = 0

        for layer_index, layer in enumerate(data):
            lines = layer.splitlines()
            new_lines = []

            for line_num, line in enumerate(lines):
                if self.getValue(line, "G"):
                    if self.getValue(line, "G") in (0, 1, 2, 3, 92):
                        if self.getValue(line, "E"):
                            current_e = self.getValue(line, "E")
                            last_move_retraction = current_e < previous_e and current_e + 1000 > previous_e
                            previous_e = current_e

                            last_extrusion_move_layer = layer_index
                            last_extrusion_move_index = len(new_lines) + 1
                new_lines.append(line)

                if line.startswith((";TYPE")):
                    match line.strip():
                        case ";TYPE:SUPPORT" | ";TYPE:SUPPORT-INTERFACE":
                            if not in_support_section:
                                if not last_move_retraction:
                                    new_retract_comment = f"; SupportEntryExitRetract adding a retract"
                                    new_retract_line = f"G1 E{round(current_e - retract_distance,5)} F{retract_speed}"
                                    # We need to insert a retraction after the last extrusion
                                    if last_extrusion_move_layer == layer_index:
                                        new_lines.insert(last_extrusion_move_index, new_retract_comment)
                                        new_lines.insert(last_extrusion_move_index + 1, new_retract_line)
                                    else:
                                        data[last_extrusion_move_layer] = self.insert_into_layer_at(data[last_extrusion_move_layer], last_extrusion_move_index, new_retract_comment, new_retract_line)
                                    new_extrude_comment = f"; SupportEntryExitRetract adding an unretract"
                                    new_extrude_line = f"G1 E{current_e} F{retract_speed}"
                                    new_lines.append(new_extrude_comment)
                                    new_lines.append(new_extrude_line)
                                in_support_section = True
                        case _:
                            if in_support_section:
                                if not last_move_retraction:
                                    new_retract_comment = f"; SupportEntryExitRetract adding a retract"
                                    new_retract_line = f"G1 E{round(current_e - retract_distance,5)} F{retract_speed}"
                                    # We need to insert a retraction after the last extrusion
                                    if last_extrusion_move_layer == layer_index:
                                        new_lines.insert(last_extrusion_move_index, new_retract_comment)
                                        new_lines.insert(last_extrusion_move_index + 1, new_retract_line)
                                    else:
                                        data[last_extrusion_move_layer] = self.insert_into_layer_at(data[last_extrusion_move_layer], last_extrusion_move_index, new_retract_comment, new_retract_line)
                                    new_extrude_comment = f"; SupportEntryExitRetract adding an unretract"
                                    new_extrude_line = f"G1 E{current_e} F{retract_speed}"
                                    new_lines.append(new_extrude_comment)
                                    new_lines.append(new_extrude_line)
                                in_support_section = False
            new_layer = "\n".join(new_lines) + "\n"
            data[layer_index] = new_layer
        return data

    def insert_into_layer_at(self, layer, line_num, *new_lines):
        layer_lines = layer.splitlines()

        for new_count, new_line in enumerate(new_lines):
            layer_lines.insert(line_num + new_count, new_line)

        new_layer = "\n".join(layer_lines) + "\n"
        return new_layer
