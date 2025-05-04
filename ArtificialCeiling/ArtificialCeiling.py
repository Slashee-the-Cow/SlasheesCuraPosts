# Artificial Ceiling by Slashee the Cow
# Clamps the maximum Z height of the nozzle to the specified height.
# If this sounds useless I wanted a big Z-hop but not to go any higher than needed when printing the upper layers.

# V1: Initial version

from .. Script import Script

class ArtificialCeiling(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Artificial Ceiling",
            "key": "ArtificialCeiling",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "max_height":
                {
                    "label": "Maximum nozzle height",
                    "description": "The highest Z value the nozzle will go to",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 10,
                    "minimum_value": 1,
                    "maximum_value_warning": 200
                }
            }
        }"""

    def execute(self, data):
        max_height = float(self.getSettingValueByKey("max_height"))

        for layer_index, layer in enumerate(data):
            if ";LAYER:" not in layer:
                continue
            layer_lines = layer.splitlines()
            for line_index, line in enumerate(layer_lines):
                if line.startswith(("G0", "G1", "G2", "G3")):
                    if "Z" in line:
                        line_z = self.getValue(line, "Z")
                        if line_z is None:
                            continue
                        try:
                            float_line_z = float(line_z)
                        except:
                            continue
                        if float_line_z > max_height:
                            layer_lines[line_index] = self.putValue(line, Z=max_height)
            data[layer_index] = "\n".join(layer_lines) + "\n"

        return data
