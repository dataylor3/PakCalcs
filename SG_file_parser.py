import json
import re
import forallpeople as si
si.environment("mystructural", top_level=True)
from collections import defaultdict
from typing import Dict, Any


class sgFileParser:
    def __init__(self, file_path):
        self.title_to_duration = {
            r"\bDead\b": 0.57,
            r"\bLive\b": 0.80,
            r"\bWind\b": 1.00
            }
        self.data = {}
        self.units = {}
        self.titles = {}
        self.combinations = {}
        self.design_actions_parsed: Dict[int, Dict[int, Dict[int, Dict[str, float]]]] = defaultdict(lambda: defaultdict(dict))
        self.VAL_KEYS = ["x", "Ax", "Vy", "Vz", "Mx", "My", "Mz"]
        self._parse(file_path)
        self.assign_k1()


    def _parse(self, file_path):
        current_handler = None
        current_section = None
        method_name = ""


        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue

                if line.startswith("UNITS"):
                        method_name = f"handle_units"
                        current_section = "UNITS"
                        current_handler = getattr(self, method_name, self.handle_generic)
                        current_handler(current_section, line)            
                else:
                    if line.isupper() and len(line.split(",")) < 2:
                        current_section = line
                    # Look for a method named "handle_HEADERNAME"
                    # Default to self.handle_generic if not found
                        method_name = f"handle_{current_section.lower().replace(' ', '_')}"
                current_handler = getattr(self, method_name, self.handle_generic)
                    
                if current_section not in self.data:
                        self.data[current_section] = {}
                elif current_handler:
                    current_handler(current_section, line)

    # --- Specific Handlers (Extensible) ---
    def handle_units(self, section, line):
        """Custom logic for UNITS: splitting by colon."""
        # Remove the leading "UNITS " 
        clean = line.replace("UNITS ", "", 1)
        # Split into key:value pairs
        pairs = [p.strip() for p in clean.split(",")]
        # Build a dictionary of units
        for p in pairs:
            if ":" in p:
                key, value = p.split(":", 1)
                self.units[key.strip().upper()] = value.strip()

    def handle_titles(self, section, line):
        mt = re.match(r'^\s*(\d+)\s*,\s*\"(.*)\"\s*$', line)
        if mt:
            lc_num = int(mt.group(1))
            lc_title = mt.group(2)
            self.titles.setdefault(lc_num, {})
            self.titles[lc_num]["title"]=lc_title

    def handle_combinations(self, section, line):
        m = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d\.Ee\-\+]+)', line)
        if m:
            #combination_num = int(m.group(1))
            combo_id = int(m.group(1))
            primary_id = int(m.group(2))
            self.combinations.setdefault(combo_id, {}).setdefault("primaries", []).append(primary_id)

    def handle_member_intermediate_forces_and_moments(self, section, line):
        unit_strs = [self.units.get("LENGTH"),
                     self.units.get("FORCE"),
                     self.units.get("FORCE"),
                     self.units.get("FORCE"),
                     self.units.get("MOMENT"),
                     self.units.get("MOMENT"),
                     self.units.get("MOMENT")]
        # Map a unit *string* to the corresponding si.<unit> variable
        _name_to_unit = {
            "m": si.m, "kN": kN, "kNm": kNm
            }
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 10:
            #print(f'Wrong length: {len(parts)}')
            return  # skip malformed/wrapped lines; adjust if your file wraps
        try:
            clc = int(parts[0])
            if clc == 12:
                print("DEBUG: Processing line for clc=12:", line)
            member = int(parts[1])
            pos = int(parts[2])
            vals = list(map(lambda s: round(float(s), 10), parts[3:]))  # x, Ax, Vy, Vz, Mx, My, Mz
            quantities = [v * _name_to_unit[u] for v, u in zip(vals, unit_strs)]
        except ValueError:
            return  # skip malformed lines
        if clc != 0:
            if clc == 12:
                print("DEBUG: Processing line for clc=12:", quantities)

            self.design_actions_parsed[clc][member][pos] = dict(zip(self.VAL_KEYS, quantities))
#        print(json.dumps(self.design_actions_parsed, indent=2))
        

    def handle_generic(self, section, line):
        """Fallback handler for simple key=value pairs."""
        pass

    # --- Assign k1 to all load cases
    def assign_k1(self):
        """I need to loop through the titles dictionary, 
        check if a load case is in the combinations dictionary 
        and if it isn't I need to assign a K1 value as a new key value pair 
        in the titles dictionary based on the values in the totles_to_duration dictionary.
        If the load case is in the combinations dictionary, I need to assign a K1 value
        that is the maximum value of the k1 values in the primary load cases"""
        for lc_num in self.titles:
            if (lc_num) not in self.combinations:
                title = self.titles[lc_num]["title"]
                k1 = 0
                for pattern, d in self.title_to_duration.items():
                    if re.search(pattern, title, re.IGNORECASE):
                        k1 = d
                        break
                self.titles[lc_num]["k1"] = k1
            else:
                # Find the maximum k1 value among primary load cases in this combination
                max_k1 = 0
                for primary_id in self.combinations[(lc_num)]["primaries"]:
                    if (primary_id) in self.titles:
                        max_k1 = max(max_k1, self.titles[(primary_id)]["k1"])
                self.titles[lc_num]["k1"] = max_k1

if __name__ == "__main__":
#    file_path = r"C:\Users\datho\PythonProjects\PakCalcs\3d Frame.TXT"
    file_path = r"C:\Users\DATaylor\Documents\Personal\PakCalcs\PakCalcs\3d Frame.TXT"
    parser = sgFileParser(file_path)
#    print(parser.data)
#    print(parser.units.get("LENGTH"))
#    print(parser.units.get("FORCE"))
#    print(parser.units.get("MOMENT"))
#    print(parser.titles)
#    print(parser.titles)
#    print(dict(parser.design_actions_parsed))
#    print(json.dumps(parser.design_actions_parsed, indent=2))
    """    
    for k, v in parser.design_actions_parsed.items():
        try:
            print(k, v)
        except Exception as e:
            print("ERROR on key:", k, "->", e)
    """
    for k, v in parser.design_actions_parsed.items():
        print("KEY:", k)
        print("VALUE:", v)   # this will crash on the problematic one
