import plotly.graph_objects as go
import forallpeople as si
# Load SI base + derived units
si.environment("mystructural", top_level=True)
from pprint import pprint


class MemberPlotter:
    def __init__(self, globalised_data, x_unit="m", action_units=None):
        """
        globalised_data: dict in the form
            element -> x_global -> load_case -> {actions}

        x_unit: unit string for x-axis (e.g. "m", "mm")
        action_units: dict mapping action names to units, e.g.
            {"Ax": "kN", "Vy": "kN", "Mz": "kNm"}
        """
        self.data = globalised_data
        self.x_unit = x_unit
        self.action_units = self.extract_action_units(globalised_data)

    @staticmethod
    def extract_action_units(data):
        units = {}
        for element_dict in data.values():
            for x_global_dict in element_dict.values():
                for actions in x_global_dict.values():
                    for name, qty in actions.items():
                        units[name] = "k"+str(qty.split()[1])[6:]  # e.g. "kN", "kNm"

        return units

    # ---------------------------------------------------------
    # INTERNAL: flatten into tidy rows for Plotly
    # ---------------------------------------------------------
    def _flatten(self):
        rows = []

        for element, x_dict in self.data.items():
            for x_global, lc_dict in x_dict.items():
                x_val = x_global.value
                for load_case, actions in lc_dict.items():
                    for action_name, action_value in actions.items():
                        z_val = (action_value.value/1000)
                        rows.append({
                            "element": element,
                            "x": x_val,
                            "load_case": load_case,
                            "action": action_name,
                            "value": z_val,
                        })
        return rows

    # ---------------------------------------------------------
    # PUBLIC: 3D plot for a chosen action (e.g. "Mz")
    # ---------------------------------------------------------
    def plot_3d(self, action="Mz"):
        rows = self._flatten()

        # Filter for the chosen action
        rows = [r for r in rows if r["action"] == action]

        fig = go.Figure()

        # One trace per load case
        load_cases = sorted({r["load_case"] for r in rows})

        for lc in load_cases:
            lc_rows = [r for r in rows if r["load_case"] == lc]

            fig.add_trace(go.Scatter3d(
                x=[r["x"] for r in lc_rows],
                y=[lc] * len(lc_rows),
                z=[r["value"] for r in lc_rows],
                mode="lines+markers",
                name=f"LC {lc}",
                marker=dict(size=2, opacity=0.8),
                line=dict(width=2),
            ))

        # Axis labels with units
        z_unit = self.action_units.get(action, "")

        fig.update_layout(
            scene=dict(
                xaxis_title=f"Global x [{self.x_unit}]",
                yaxis_title="Load Case",
                zaxis_title=f"{action} [{z_unit}]",
            ),
            title=f"3D Plot of {action} Across Member",
        )

        return fig
