from py_SG_file_parser import sgFileParser
from pprint import pprint
from py_ActionData import ActionData
from py_LoadCase import LoadCase
from py_design_member import DesignMember
from py_timberClasses import beamDesign, Section, bendRestraints, Material, ModificationFactors, compRestraints
import forallpeople as si
si.environment("mystructural", top_level=True)
from pathlib import Path

class MemberDesignActions:
    def __init__(self, elements:list, load_cases:list, all_design_actions: dict, lc_titles: dict ):
        self.elements = elements
        self.load_cases = load_cases
        self.all_design_actions = all_design_actions
        self.lc_titles = lc_titles
        #self.load_case_details = load_case_details
        self.filtered = self.filter_design_actions()
        self.pivot = self.pivot_to_element_x_loadcase(self.filtered)
        self.globalized = self.make_x_global(self.pivot, self.elements)
        self.design_action_data = self.to_load_cases(self.lc_titles)

    def filter_design_actions(self):
        """
        I need to loop through the design actions and filter them 
        based on the elements and load cases in the design members. 
        I need to return a dictionary of the filtered design actions.
        """
        filtered_design_actions = {
            top: {
                mid: inner
                for mid, inner in mids.items()
                if mid in self.elements
            }
            for top, mids in self.all_design_actions.items()
            if top in self.load_cases
        } 
        #print("Top-level keys:", list(self.all_design_actions.keys()))
        #print("load_cases:", self.load_cases)
        #print("Second-level keys:", {k: list(v.keys()) for k, v in self.all_design_actions.items()})
        #print("elements:", self.elements)
       
        return filtered_design_actions

    def pivot_to_element_x_loadcase(self, data):
        new = {}

        for load_case, elements in data.items():
            for element, positions in elements.items():

                # Ensure element exists in new structure
                if element not in new:
                    new[element] = {}

                for pos_id, record in positions.items():
                    x_val = record["x"]
                    record_no_x = {k: v for k, v in record.items() if k != "x"}

                    # Ensure x exists under this element
                    if x_val not in new[element]:
                        new[element][x_val] = {}

                    # Insert load case under this x
                    new[element][x_val][load_case] = record_no_x

        return new

    def make_x_global(self, data, element_order):
        """
        data: {element: {x_local: {load_case: data}}}
        element_order: [5, 6, 13, ...] in correct physical order
        """

        new = {}
        cumulative = 0

        for element in element_order:
            new[element] = {}

            # Get all x positions for this element
            x_positions = sorted(data[element].keys())

            # Compute element length (max local x)
            element_length = x_positions[-1]

            for x_local in x_positions:
                x_global = cumulative + x_local
                new[element][x_global] = data[element][x_local]

            cumulative = cumulative + element_length

        return new

    def to_action_data(self):
        # Prepare empty lists for each load case
        load_case_data = {
            lc: {"x": [], "Mz": [], "My": [], "Vy": [], "Vz": [], "Ax": []}
            for lc in self.load_cases
        }

        # Loop through globalised structure
        for element, x_dict in self.globalized.items():
            for x_global, lc_dict in x_dict.items():
                for lc, actions in lc_dict.items():
                    load_case_data[lc]["x"].append(x_global)
                    load_case_data[lc]["Mz"].append(actions["Mz"])
                    load_case_data[lc]["My"].append(actions["My"])
                    load_case_data[lc]["Vy"].append(actions["Vy"])
                    load_case_data[lc]["Vz"].append(actions["Vz"])
                    load_case_data[lc]["Ax"].append(actions["Ax"])

        # Convert each load case into an ActionData object
        action_objects = {}
        for lc, arrays in load_case_data.items():
            action_objects[lc] = ActionData(
                x=arrays["x"],
                Mz=arrays["Mz"],
                My=arrays["My"],
                Vy=arrays["Vy"],
                Vz=arrays["Vz"],
                Ax=arrays["Ax"],
            )

        return action_objects

    def to_load_cases(self, load_case_details: dict):
        """
        load_case_details: dict like
            {1: {'k1': 0.57, 'title': 'Dead Load'}, ...}
        """

        action_data = self.to_action_data()
        load_cases = []

        for lc_id in self.load_cases:
            details = load_case_details[lc_id]

            lc = LoadCase(
                id=lc_id,
                title=details["title"],
                K1=details["k1"],
                actions=action_data[lc_id]
            )

            load_cases.append(lc)

        return load_cases

if __name__ == "__main__":
    primary_path = r"C:\Users\datho\PythonProjects\PakCalcs\3d Frame 260317.TXT"
    fallback_path = r"C:\Users\DATaylor\Documents\Personal\PakCalcs\PakCalcs\3d Frame 260317.TXT"
    file_path = primary_path if Path(primary_path).exists() else fallback_path
    
    parser = sgFileParser(file_path)
    
    members = DesignMember.build_many(parser.design_members)
    #print((list(members[0])))

    des_act = MemberDesignActions(list(members[0].element_list), [11,12,13,14,15,16], parser.design_actions_parsed, parser.titles)
    rafter_section = Section(name="rafter", d=190*mm, b=45*mm)
    material = Material(name="LVL", f_prime_b=8*MPa, f_prime_s=0.5*MPa, f_prime_c=10*MPa, f_prime_t=6*MPa, rho_b=0.85, rho_c=0.9)
    rafter_restraints = bendRestraints(L_ayT=200*mm, L_ayB=4200*mm, L_alphaT=2100*mm, L_alphaB=2100*mm, 
                                        material=material, section=rafter_section)
    column_restraints = compRestraints(g_13=1.5, L=4000*mm, L_ax = 4000*mm, L_ay=2100*mm,
                                       x_cont_res = False, y_cont_res = False,
                                       material=material, section=rafter_section)
    mod_factors = ModificationFactors(k_4=1.0, k_6=1.0, k_9=1.0)

    rafter = beamDesign(section=rafter_section, bendrestraints=rafter_restraints,
                   material=material, mod_factors=mod_factors, comprestraints=column_restraints)
    
    #rafterMd, rafterUtil = rafter.checkM_dx(k1=0.57, M_starx=-1.173*Nm)
    #print(f"Capacity: {rafterMd} Utilization: {rafterUtil}")


    
    for lc in des_act.design_action_data:
        print("Load Case ID:", lc.id)
        print("Load Case:", lc.title)
        print("K1:", lc.K1)
        #print("Actions Mz:", (lc.actions.Mz))  # print first 5 for brevity
        #print("Actions x:", (lc.actions.x))
        k1 = lc.K1
        for point in lc.actions.My:
            rafterMd, rafterUtil = rafter.checkM_dy(k1=k1, M_stary=point)
            print(f"Capacity: {rafterMd} Action: {point} Utilization: {rafterUtil:.2f}")
        
        for x, Mx, My in zip(lc.actions.x, lc.actions.Mz, lc.actions.My):
            rafterUtil = rafter.check_combined_Mx_My(M_starx=Mx, M_stary=My, k1=k1)
            print(f"Biaxial bending Utilization: {rafterUtil:.2f} at x={x} with Mx={Mx:.2f} and My={My:.2f}")

        for x, Vy, Vz in zip(lc.actions.x, lc.actions.Vy, lc.actions.Vz):
            rafterVdy, rafterVUtily = rafter.checkV(k1=k1, V_star=Vy)
            rafterVdz, rafterVUtilz = rafter.checkV(k1=k1, V_star=Vz)
            print(f"Shear Utilization: {rafterVUtily:.2f} at x={x} with Vy={Vy:.2f} and Vd={rafterVdy:.2f}")
            print(f"Shear Utilization: {rafterVUtilz:.2f} at x={x} with Vz={Vz:.2f} and Vd={rafterVdz:.2f}")
        
        for x, Ax in zip(lc.actions.x, lc.actions.Ax):
            if Ax > 0:
                rafterNdx, rafterNdy, rafterUtilx, rafterUtildy = rafter.checkN_d(k1=k1, N_star=Ax)
                print(f"X-axis Axial Utilization: {rafterUtilx:.2f} at x={x} with Ax={Ax:.2f} and Ndx={rafterNdx:.2f}")
                print(f"Y-axis Axial Utilization: {rafterUtildy:.2f} at x={x} with Ax={Ax:.2f} and Ndy={rafterNdy:.2f}")
            else:
                rafterNdt, rafterUtilt = rafter.checkN_dt(k1=k1, N_star=Ax)
                print(f"Tension Axial Utilization: {rafterUtilt:.2f} at x={x} with Ax={Ax:.2f} and Ndt={rafterNdt:.2f}")
    #pprint(des_act.max_moment())
    
