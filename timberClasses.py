import forallpeople as si
si.environment("mystructural", top_level=True)
from math import pi
import re
import json
from typing import Dict, Callable, Optional


class beamDesign():
    def __init__(self, d:si.Physical, b:si.Physical, L:si.Physical, L_ayT:si.Physical,
                  L_ayB:si.Physical, L_aphaT:si.Physical, L_aphaB:si.Physical, rho_b:float,
                  f_prime_b:si.Physical, phi:float = 0.95, k_4:float = 1.0, k_6:float = 1.0,
                  k_9:float = 1.0):
        """
        Parameters
        d: Depth of the beam
        b: Width of the beam
        L: Span of the beam
        L_ayT: Spacing of discrete lateral restraints on the top of the beam
        L_ayB: Spacing of discrete lateral restraints on the bottom of the beam
        L_aphaT: Spacing of discrete torsional restraints on the top of the beam
        L_aphaB: Spacing of discrete torsional restraints on the bottom of the beam
        rho_b: Material factor from AS1720
        f_prime_b: Characteristic bending strength of the beam
        phi: Capacity reduction factor
        k_4: Moisture content factor    
        k_6: Temperature factor
        k_9: Strength sharing factor
        designActions: Design actions on the beam
        """

        self.phi = phi
        self.d = d
        self.b = b
        self.L = L
        self.L_ayT = L_ayT
        self.L_ayB = L_ayB
        self.L_aphaT = L_aphaT
        self.L_aphaB = L_aphaB
        self.rho_b = rho_b
        self.cont_res_limit = self.d*64*(self.b/(self.rho_b*self.d))**2
        self.Z_x = (b*d**2)/6  # Section modulus for rectangular section
        self.Z_y = (d*b**2)/6  # Section modulus for rectangular section
        self.f_prime_b = f_prime_b
        self.k_4 = k_4
        self.k_6 = k_6
        self.k_9 = k_9
        # self.designActions = designActions
        # self.material = material

    @property
    def S_1Sag(self):
        if self.L_ayT <= self.cont_res_limit: # Continuous restraint to top/compression edge
            s_top = 0.0
            #print(f's_top sag case 1: {s_top}')
        else: # Discrete restraint to top/compression edge
            s_top = 1.25*(self.d/self.b)*(self.L_ayT/self.d)**0.5
            #print(f's_top sag case 2: {s_top}')
        if self.L_ayB <= self.cont_res_limit: # Continuous restraint to bottom/tension edge
            s_bottom = 2.25*self.d/self.b
            #print(f's_bottom sag case 1: {s_bottom}')
        else: # Discrete restraint to bottom/tension edge
            s_bottom1 = (self.d/self.b)**1.35*(self.L_ayT/self.d)**0.25 # Discrete restraints to bottom/tension edge
            #print(f's_bottom1 sag case 2a: {s_bottom1}')
            s_bottom2 = 1.5*self.d/self.b/((pi*self.d/self.L_aphaT)**2+0.4)**0.5 # Discrete torsional restraints to top/compression edge
            #print(f's_bottom2 sag case 2b: {s_bottom2}')
            s_bottom = min(s_bottom1, s_bottom2)
            #print(f's_bottom sag case 2: {s_bottom}')
        return min(s_top, s_bottom)
        
    @property
    def S_1Hog(self):
        if self.L_ayT <= self.cont_res_limit: # Continuous restraint to top/tension edge
            s_top = 2.25*self.d/self.b
            #print(f's_top hog case 1: {s_top}')
        else:
            s_top1 = (self.d/self.b)**1.35*(self.L_ayT/self.d)**0.25 # Discrete restraints to top/tension edge
            #print(f's_top1 hog case 2a: {s_top1}')
            s_top2 = 1.5*self.d/self.b/((pi*self.d/self.L_aphaB)**2+0.4)**0.5 # Discrete torsional restraints to bottom/compression edge
            #print(f's_top2 hog case 2b: {s_top2}')
            s_top = min(s_top1, s_top2)
            #print(f's_top hog case 2: {s_top}')
        if self.L_ayB <= self.cont_res_limit: # Continuous restraint to bottom/compression edge
            s_bottom = 0
            #print(f's_bottom hog case 1: {s_bottom}')
        else:
            s_bottom = 1.25*(self.d/self.b)*(self.L_ayB/self.d)**0.5
            #print(f's_bottom hog case 2: {s_bottom}')
        return min(s_top, s_bottom)

    def k_12(self, S_1:float):
        #print(f'S_1: {S_1}')
        if self.rho_b*S_1 <=10:
            return 1.0
        elif 10<= self.rho_b*S_1 <20:
            return 1.5-0.05*(self.rho_b*S_1)
        else:
            return 200/(self.rho_b*S_1)**2

    @property
    def k_12Sag(self):
        return self.k_12(self.S_1Sag)

    @property
    def k_12Hog(self):
        return self.k_12(self.S_1Hog)
    
    def M_d(self, k_1:float, k_12:float):
        return self.phi*k_1*self.k_4*self.k_6*self.k_9*k_12*self.f_prime_b*self.Z_x

    @property
    def M_d5secSag(self):
        return self.M_d(k_1=1.0, k_12=self.k_12Sag)

    @property
    def M_d5secHog(self):
        return self.M_d(k_1=1.0, k_12=self.k_12Hog)

    @property
    def M_d5minSag(self):
        return self.M_d(k_1=1.0, k_12=self.k_12Sag)

    @property
    def M_d5minHog(self):
        return self.M_d(k_1=1.0, k_12=self.k_12Hog)

    @property
    def M_d5hrSag(self):
        return self.M_d(k_1=0.97, k_12=self.k_12Sag)

    @property
    def M_d5hrHog(self):
        return self.M_d(k_1=0.97, k_12=self.k_12Hog)

    @property
    def M_d5daySag(self):
        return self.M_d(k_1=0.94, k_12=self.k_12Sag)

    @property
    def M_d5dayHog(self):
        return self.M_d(k_1=0.94, k_12=self.k_12Hog)

    @property
    def M_d5monSag(self):
        return self.M_d(k_1=0.80, k_12=self.k_12Sag)

    @property
    def M_d5monHog(self):
        return self.M_d(k_1=0.80, k_12=self.k_12Hog)

    @property
    def M_d50yrSag(self):
        return self.M_d(k_1=0.57, k_12=self.k_12Sag)

    @property
    def M_d50yrHog(self):
        return self.M_d(k_1=0.57, k_12=self.k_12Hog)

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
                    else:
                        if s and not s[0].isdigit():
                            in_titles = False

        # Build the JSON object (dict) keyed by load case number
        # If you prefer string keys in the final JSON, convert here; otherwise keep ints.
        result = {num: titles_map.get(num, "") for num in sorted(primary_set)}
        #return result
        return {num: titles_map.get(num, "") for num in sorted(primary_set)}

        """
        # Example usage:
        if __name__ == "__main__":
            path = "3d Frame.TXT"  # update to your file path
            obj = extract_primary_load_cases_as_object(path)
            # Pretty print JSON object to stdout
            print(json.dumps(obj, indent=2))
        """


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



    """
    def calculate_bending_moment(self):
        # Simple formula for maximum bending moment in a simply supported beam
        return (self.designActions.load * self.span**2) / 8

    def calculate_shear_force(self):
        # Simple formula for maximum shear force in a simply supported beam
        return (self.designActions.load * self.span) / 2
    def design_beam(self):
        bending_moment = self.calculate_bending_moment()
        shear_force = self.calculate_shear_force()
        
        # Placeholder for actual design logic based on material properties
        print(f"Designing beam with span: {self.span} m, load: {self.load} kN/m")
        print(f"Maximum Bending Moment: {bending_moment} kNm")
        print(f"Maximum Shear Force: {shear_force} kN")
        print(f"Using material: {self.material}")
    """

if __name__ == "__main__":
    # Example usage
    beam = beamDesign(d=190*mm, b=45*mm, L=4.2*m,
                        L_ayT=300*mm, L_ayB=2100*mm,
                        L_aphaT=4200*m, L_aphaB=4200*mm,
                        rho_b=0.81, f_prime_b=19*MPa)
    #print("S_1Sag:", beam.S_1Sag)
    #print("S_1Hog:", beam.S_1Hog)
    lctitles = beam.get_primary_load_cases("C:/Users/DATaylor/Documents/Personal/PakCalcs/PakCalcs/3d Frame.TXT")
    
    title_to_duration = {
        r"\bDead\b": 0.57,
        r"\bLive\b": 0.80,
        r"\bWind\b": 1.00
    }
    case_data = beam.build_case_data_with_duration(lctitles, title_rules=title_to_duration)
    print(case_data)


    print("k_12Sag:", beam.k_12Sag)
    print("k_12Hog:", beam.k_12Hog)

    print("M_d5secSag:", beam.M_d5secSag)
    print("M_d5secHog:", beam.M_d5secHog)
    print("M_d5minSag:", beam.M_d5minSag)
    print("M_d5minHog:", beam.M_d5minHog)
    print("M_d5hrSag:", beam.M_d5hrSag)
    print("M_d5hrHog:", beam.M_d5hrHog)
    print("M_d5daySag:", beam.M_d5daySag)
    print("M_d5dayHog:", beam.M_d5dayHog)
    print("M_d5monSag:", beam.M_d5monSag)
    print("M_d5monHog:", beam.M_d5monHog)
    print("M_d50yrSag:", beam.M_d50yrSag)
    print("M_d50yrHog:", beam.M_d50yrHog)

    print ("Primary Load Cases Titles:", json.dumps(lctitles, indent = 2))
    print(lctitles)

