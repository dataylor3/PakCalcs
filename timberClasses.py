import forallpeople as si
si.environment("mystructural", top_level=True)
from math import pi


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
            print(f's_top sag case 1: {s_top}')
        else: # Discrete restraint to top/compression edge
            s_top = 1.25*(self.d/self.b)*(self.L_ayT/self.d)**0.5
            print(f's_top sag case 2: {s_top}')
        if self.L_ayB <= self.cont_res_limit: # Continuous restraint to bottom/tension edge
            s_bottom = 2.25*self.d/self.b
            print(f's_bottom sag case 1: {s_bottom}')
        else: # Discrete restraint to bottom/tension edge
            s_bottom1 = (self.d/self.b)**1.35*(self.L_ayT/self.d)**0.25 # Discrete restraints to bottom/tension edge
            print(f's_bottom1 sag case 2a: {s_bottom1}')
            s_bottom2 = 1.5*self.d/self.b/((pi*self.d/self.L_aphaT)**2+0.4)**0.5 # Discrete torsional restraints to top/compression edge
            print(f's_bottom2 sag case 2b: {s_bottom2}')
            s_bottom = min(s_bottom1, s_bottom2)
            print(f's_bottom sag case 2: {s_bottom}')
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

    @property
    def k_12Sag(self):
        return self.k_12(self.S_1Sag)

    @property
    def k_12Hog(self):
        return self.k_12(self.S_1Hog)
    
    def k_12(self, S_1:float):
        #print(f'S_1: {S_1}')
        if self.rho_b*S_1 <=10:
            return 1.0
        elif 10<= self.rho_b*S_1 <20:
            return 1.5-0.05*(self.rho_b*S_1)
        else:
            return 200/(self.rho_b*S_1)**2






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
    beam = beamDesign(d=300*mm, b=40*mm, L=10*m,
                        L_ayT=10000*mm, L_ayB=10000*mm,
                        L_aphaT=1000*m, L_aphaB=10000*mm,
                        rho_b=1.0, f_prime_b=19*MPa)
    #print("S_1Sag:", beam.S_1Sag)
    #print("S_1Hog:", beam.S_1Hog)
    print("k_12Sag:", beam.k_12Sag)
    print("k_12Hog:", beam.k_12Hog)