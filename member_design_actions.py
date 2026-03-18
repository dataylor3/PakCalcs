from SG_file_parser import sgFileParser
from pprint import pprint

class MemberDesignActions:
    def __init__(self, elements:list, load_cases:list, all_design_actions: dict):
        self.elements = elements
        self.load_cases = load_cases
        self.all_design_actions = all_design_actions
        self.filtered = self.filter_design_actions()
        self.pivot = self.pivot_to_element_x_loadcase(self.filtered)
        self.globalized = self.make_x_global(self.pivot, self.elements)

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





if __name__ == "__main__":
    file_path = r"C:\Users\datho\PythonProjects\PakCalcs\3d Frame.TXT"
#    file_path = r"C:\Users\DATaylor\Documents\Personal\PakCalcs\PakCalcs\3d Frame.TXT"
    parser = sgFileParser(file_path)
    des_act = MemberDesignActions([13,21,5,16], [11,12,13], parser.design_actions_parsed)
    pprint(des_act.globalized)

