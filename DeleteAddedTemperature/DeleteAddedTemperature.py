# Delete Added Temperature by Slashee the Cow
# Not the first and probably won't be the last single purpose script I write to work around a bug.
# Version 1

from ..Script import Script
from UM.Application import Application

class DeleteAddedTemperature(Script):
    def __init__(self):
        super().__init__()


    def getSettingDataString(self):
        return """{
            "name": "Delete Added Temperature",
            "key": "DeleteAddedTemperature",
            "metadata": {},
            "version": 2,
            "settings": {}
        }"""

    def execute(self, data):
        new_layer = []
        delete_mode = False

        startup_layer = data[1].split("\n")
        for line in startup_layer:
            if not delete_mode:
                if line.startswith(";Generated with"):
                    delete_mode = True
                new_layer.append(line)
            else:
                match line.split()[0]:
                    case "M104" | "M105" | "M109" | "M140" | "M141" | "M190" | "M191":
                        continue
                    case _:
                        delete_mode = False
                        new_layer.append(line)

        layer_1 = "\n".join(new_layer)
        data[1] = layer_1
        return data
