# Limit Support Acceleration: A script by Slashee the Cow
# Because my new E3V3SE pulled supports out as it printed
# That's _MY_ job

from ..Script import Script
from UM.Application import Application

class LimitSupportAcceleration(Script):
    def __init__(self):
        super().__init__()

        self.accel_cura_settings = {}

    def getSettingDataString(self):
        return """{
            "name": "Limit Support Acceleration",
            "key": "LimitSupportAcceleration",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "speed_limit":
                {
                    "label": "Acceleration limit",
                    "description": "Maximum acceleration rate for both X and Y axes during support sections. Applies to all axes.",
                    "unit": "mm/s²",
                    "type": "float",
                    "default_value": "400.0",
                    "minimum_value": "1",
                    "minimum_value_warning": "100",
                    "maximum_value_warning": "1000"
                }
            }
        }"""

    def execute(self, data):
        global_stack = Application.getInstance().getGlobalContainerStack()

        self.accel_cura_settings["x"] = global_stack.getProperty("machine_max_acceleration_x", "value")
        self.accel_cura_settings["y"] = global_stack.getProperty("machine_max_acceleration_y", "value")
        self.accel_cura_settings["default"] = global_stack.getProperty("machine_acceleration", "value")

        max_support_speed = int(self.getSettingValueByKey("speed_limit"))

        in_support_section = False
        for layer_index, layer in enumerate(data):
            lines = layer.split("\n")
            new_lines = []
            for line_num, line in enumerate(lines):
                new_lines.append(line)
                if line.startswith(";TYPE:"):
                    match line.strip():
                        case ";TYPE:SUPPORT" | ";TYPE:SUPPORT-INTERFACE":
                            if not in_support_section:
                                # Honey, we hit a support!
                                in_support_section = True
                                new_lines.append(f"M201 X{int(max_support_speed)} Y{int(max_support_speed)} ; Supports go slow :(")

                        case _:
                            if in_support_section:
                                # Honey, we're out of the supports!
                                in_support_section = False
                                new_lines.append(f"M201 X{int(self.accel_cura_settings.get('x'))} Y{int(self.accel_cura_settings.get('y'))} ; Out of support, we can go fast again!")
            final_lines = "\n".join(new_lines)
            data[layer_index] = final_lines
        return data
