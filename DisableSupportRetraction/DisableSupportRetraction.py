# Disable Support Retraction
# By Slashee the Cow for CBX_Micha
# Shine on, you crazy... whatever you are.
# Version 1

from ..Script import Script
from UM.Application import Application

class DisableSupportRetraction(Script):
    def __init__(self):
        super().__init__()


    def getSettingDataString(self):
        return """{
            "name": "Disable Support Retraction",
            "key": "DisableSupportRetraction",
            "metadata": {},
            "version": 2,
            "settings": {}
        }"""

    def execute(self, data):
        #global_stack = Application.getInstance().getGlobalContainerStack()

        for layer_index, layer in enumerate(data):
            lines = layer.split("\n")
            new_lines = []
            is_retracted = False
            in_support_section = False
            in_support_needs_prime = False
            #end_support_needs_retract = False

            support_last_retract_index = 0
            support_last_retract_line = ""
            max_e = 0
            for line_num, line in enumerate(lines):
                #new_lines.append(line)
                E_value = self.getValue(line, "E")
                if E_value:
                    if E_value > max_e:
                        max_e = E_value
                        is_retracted = False
                    elif E_value < max_e:
                        is_retracted = True
                        if in_support_section:
                            support_last_retract_index = len(new_lines)
                            support_last_retract_line = line

                if line.startswith(";TYPE:"):
                    match line.strip():
                        case ";TYPE:SUPPORT" | ";TYPE:SUPPORT-INTERFACE":
                            if not in_support_section:
                                # Honey, we hit a support!
                                #new_lines.append("; I just found a support!")
                                in_support_section = True
                                if is_retracted:
                                    in_support_needs_prime = True
                        case _:
                            if in_support_section:
                                # Honey, we're out of the supports!
                                #new_lines.append("; I just lost a support :(")
                                in_support_section = False
                                if is_retracted and max_e > self.getValue(support_last_retract_line,"E"):
                                    new_lines.insert(support_last_retract_index,support_last_retract_line)
                if not (self.getValue(line, "G") == 1 and E_value and not (self.getValue(line, "X") or self.getValue(line, "Y"))):
                    # This isn't a retraction line
                    new_lines.append(line)
                    continue
                #else:
                    #new_lines.append(f"; I just took out retraction line: {line}")
                # Technically this should probably be an elif but if that last one didn't go to the next iteration we have bigger problems
                if in_support_section:
                    if in_support_needs_prime:
                        new_lines.append(line)
                        in_support_needs_prime = False
                else:
                    new_lines.append(line)

            final_lines = "\n".join(new_lines)
            final_lines += "\n"
            data[layer_index] = final_lines
        return data
