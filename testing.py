import forallpeople as si
import pandas as pd
# Load SI base + derived units
si.environment("mystructural", top_level=True)
from handcalcs.decorator import handcalc
#import handcalcs.render
from math import cos, sin, radians, degrees
g_acc = 9.81*m/s**2  # gravitational acceleration
from SG_file_parser import sgFileParser
from design_member import DesignMember
from member_design_actions import MemberDesignActions
from pprint import pprint
from member_plotter import MemberPlotter
from timberClasses import beamDesign

results = sgFileParser(r"C:\Users\DATaylor\Documents\Personal\PakCalcs\PakCalcs\3d Frame 260317.TXT")
#results = sgFileParser(r"3d Frame 260317.TXT")
#print(results.units)

members = DesignMember.build_many(results.design_members)
#print((list(members[0])))

des_act = MemberDesignActions(list(members[1].element_list), [11], results.design_actions_parsed)
pprint(des_act.globalized)

action_units = {
    "Ax": results.units.get("FORCE"),
    "Vy": results.units.get("FORCE"),
    "Vz": results.units.get("FORCE"),
    "Mx": results.units.get("MOMENT"),
    "My": results.units.get("MOMENT"),
    "Mz": results.units.get("MOMENT"),
}
plotter = MemberPlotter(des_act.globalized, action_units=action_units)

fig = plotter.plot_3d(action="Vz")
fig.show()