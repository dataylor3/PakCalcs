import re
import json
from typing import Dict, Callable, Optional
from collections import defaultdict
from typing import Dict, Any
from pprint import pprint


class load_class():
    def __init__(self, id_num: int, title: str):
        self.id_num = id_num
        self.title = title


class timber_primary_load_case(load_class):
    def __init__(self, id_num: int, title: str, k1: float):
        super().__init__(id_num, title)
        self.k1 = k1


class timber_combination_load_case(load_class):
    def __init__(self, id_num: int, title: str, primary_load_cases: list[timber_primary_load_case]):
        super().__init__(id_num, title)
        self.primary_load_cases = primary_load_cases

    @property
    def k1(self):
        """
        Returns the minimum duration factor of all primary load cases in the combination.
        """
        if not self.primary_load_cases:
            return 1.0  # Default or handle as an error if no primary cases
        
        min_duration = 1.0
        for lc_data in self.primary_load_cases.values():
            if "duration_factor" in lc_data:
                min_duration = min(min_duration, lc_data["duration_factor"])
        return min_duration

        
class loading():
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.title_to_duration = {
            r"\bDead\b": 0.57,
            r"\bLive\b": 0.80,
            r"\bWind\b": 1.00
            }
        self.VAL_KEYS = ["x", "Ax", "Vy", "Vz", "Mx", "My", "Mz"]
        self.parsed: Dict[int, Dict[int, Dict[int, Dict[str, float]]]] = defaultdict(lambda: defaultdict(dict))
        self.plc_titles = self.get_primary_load_cases(file_path)
        self.loads = self.get_loads(file_path)



    def get_primary_load_cases(self, file_path: str) -> dict:
        """
        Parse a SPACE GASS text output file and return primary load cases
        (referenced in the COMBINATIONS section) as a single dictionary:
            { <load_case_number>: "<load_case_title>", ... }

        Section logic:
        - COMBINATIONS: lines in the format "<combo_num>, <primary_num>, <factor>"
            -> Collect the second column as a primary load case number.
        - TITLES: lines in the format "<case_num>, \"<title>\""
            -> Map case numbers to their titles.

        Args:
            file_path: Path to the SPACE GASS text output file.

        Returns:
            A dict mapping primary load case numbers (int) to their titles (str).
        """
        primary_set = set()
        titles_map = {}
        in_titles = False
        in_combos = False

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                s = line.strip()

                # Enter section flags
                if s.upper().startswith('TITLES'):
                    in_titles = True
                    in_combos = False
                    continue
                if s.upper().startswith('COMBINATIONS'):
                    in_combos = True
                    in_titles = False
                    continue

                # Heuristic: if we're in TITLES and hit another ALL-CAPS header, stop TITLES
                if in_titles and s and re.match(r'^[A-Z ]+$', s):
                    in_titles = False

                # Parse COMBINATIONS rows: "<comb_num>, <primary_num>, <factor>"
                if in_combos:
                    m = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d\.Ee\-\+]+)', line)
                    if m:
                        primary_num = int(m.group(2))
                        primary_set.add(primary_num)
                    else:
                        # End COMBINATIONS on first non-data line
                        if s and not s[0].isdigit():
                            in_combos = False

                # Parse TITLES rows: "<case_num>, \"<title>\""
                if in_titles:
                    mt = re.match(r'^\s*(\d+)\s*,\s*\"(.*)\"\s*$', line)
                    if mt:
                        lc_num = int(mt.group(1))
                        lc_title = mt.group(2)
                        titles_map[lc_num] = lc_title
                        #titles_map[lc_num] = lc.timber_primary_load_case(lc_num, lc_title,k1) ########
                    else:
                        if s and not s[0].isdigit():
                            in_titles = False

        # Build the JSON object (dict) keyed by load case number
        # If you prefer string keys in the final JSON, convert here; otherwise keep ints.
        result = {num: titles_map.get(num, "") for num in sorted(primary_set)}
        #return result
        return {num: titles_map.get(num, "") for num in sorted(primary_set)}

    def build_case_data_with_duration(self, 
        case_titles: Dict[int, str],
        *,
        # 1) explicit per-case overrides (highest precedence)
        per_case_duration: Optional[Dict[int, float]] = None,
        # 2) title-based rules: list of (pattern, factor); first match wins
        title_rules: Optional[Dict[str, float]] = None,
        # 3) fallback if nothing matches
        default_duration: float = 1.0,
        # optional: simple category tagging via patterns
        category_rules: Optional[Dict[str, str]] = None
    ) -> Dict[int, Dict[str, object]]:
        """
        Returns:
        {case_num: { "title": <str>, "duration_factor": <float>, "category": <str or None> } }
        Resolution order for duration_factor:
        per_case_duration[num] > first matching title_rules pattern > default_duration
        """
        per_case_duration = per_case_duration or {}
        title_rules = title_rules or {}
        category_rules = category_rules or {}

        out: Dict[int, Dict[str, object]] = {}

        for num, title in case_titles.items():
            # category via rules (pattern -> category)
            category = None
            for pat, cat in category_rules.items():
                if re.search(pat, title, flags=re.IGNORECASE):
                    category = cat
                    break

            # duration via explicit per-case override
            if num in per_case_duration:
                kd = per_case_duration[num]
            else:
                # duration via first matching title pattern
                kd = None
                for pat, val in title_rules.items():
                    if re.search(pat, title, flags=re.IGNORECASE):
                        kd = val
                        break
                # default if no rule matched
                if kd is None:
                    kd = default_duration

            out[num] = {
                "title": title,
                "duration_factor": float(kd)#,
                #"category": category
            }

        return out

    def get_loads(self, file_path: str)->dict:
        """
        I need a new method that parses the combination load cases listed in the text file and 
        for each load case (defined over multiple lines) parse the primary load case number
        (the second field), look up this primary load case in the dictionary of the primary load cases
        and extrct the lowest value of duration factor for that dictionary.  This then need to be
        saved with the combination load case title in a dictionary.
        """
        in_titles = False
        in_combos = False
        in_int_actions = False

        loads = {}

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                s = line.strip()

                # Enter section flags
                if s.upper().startswith('TITLES'):
                    in_titles = True
                    in_combos = False
                    in_int_actions = False
                    continue
                if s.upper().startswith('COMBINATIONS'):
                    in_combos = True
                    in_titles = False
                    in_int_actions = False
                    continue
                if s.upper().startswith("MEMBER INTERMEDIATE FORCES"):
                    in_combos = False
                    in_titles = False
                    in_int_actions = True
                    continue




                # Parse COMBINATIONS rows: "<comb_num>, <primary_num>, <factor>"
                if in_combos:
                    m = re.match(r'^\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d\.Ee\-\+]+)', line)
                    if m:
                        #combination_num = int(m.group(1))
                        combo_id = int(m.group(1))
                        primary_id = int(m.group(2))
                        loads.setdefault(combo_id, {}).setdefault("primaries", []).append(primary_id)
                        
                        #combination_set.add(combination_num)
                    else:
                        # End COMBINATIONS on first non-data line
                        if s and not s[0].isdigit():
                            in_combos = False

                if in_titles:
                    mt = re.match(r'^\s*(\d+)\s*,\s*\"(.*)\"\s*$', line)
                    if mt:
                        lc_num = int(mt.group(1))
                        lc_title = mt.group(2)
                        if lc_num in loads:
                            loads[lc_num]["title"] = lc_title
                    else:
                        if s and not s[0].isdigit():
                            in_titles = False
                
                
                if in_int_actions:
                    parts = [p.strip() for p in s.split(",")]
                    if len(parts) != 10:
                        #print(f'Wrong length: {len(parts)}')
                        continue  # skip malformed/wrapped lines; adjust if your file wraps
                    try:
                        clc = int(parts[0])
                        member = int(parts[1])
                        pos = int(parts[2])
                        vals = list(map(float, parts[3:]))  # x, Ax, Vy, Vz, Mx, My, Mz
                    except ValueError:
                        in_int_actions = False
                        continue
                    if clc != 0:
                        self.parsed[clc][member][pos] = dict(zip(self.VAL_KEYS, vals))
                #print(json.dumps(self.parsed, indent=2))


                


            lc_durations = self.build_case_data_with_duration(self.plc_titles, title_rules=self.title_to_duration)

            for lc, data in loads.items():
                primaries = data["primaries"]
                k1 = 0.0
                for plc in primaries:
                    k1temp = lc_durations.get(plc, {}).get("duration_factor", 1.0)
                    if k1temp > k1:
                        k1 = k1temp
                data["duration_factor"] = k1

            for clc, members in self.parsed.items():
                bucket = loads[clc].setdefault("members", {})
                for member, pos_map in members.items():
                    m = bucket.setdefault(member, {})
                    for pos, vec in pos_map.items():
                        m[pos] = vec

        return loads