import forallpeople as si
si.environment("mystructural", top_level=True)
from math import pi
import re
import json
from typing import Dict, Callable, Optional
import loadClasses as lc


class beamDesign():
    def __init__(self, d:si.Physical, b:si.Physical, L:si.Physical,
                  L_ayT:si.Physical, L_ayB:si.Physical, L_aphaT:si.Physical,
                    L_aphaB:si.Physical, rho_b:float, f_prime_b:si.Physical,
                      phi:float = 0.95, k_4:float = 1.0, k_6:float = 1.0,
                        k_9:float = 1.0, loading:lc.loading = None):
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
        self.loading = loading

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

 

    """
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
    #file_path = r""
    file_path = r"C:\Users\datho\PythonProjects\PakCalcs\3d Frame.TXT"
    member_loading = lc.loading(file_path)
    beam = beamDesign(d=190*mm, b=45*mm, L=4.2*m,
                        L_ayT=300*mm, L_ayB=2100*mm,
                        L_aphaT=4200*m, L_aphaB=4200*mm,
                        rho_b=0.81, f_prime_b=19*MPa,
                        loading = member_loading)
    
    #print(member_loading.plc_titles)
    for n in beam.loading.loads[13]["members"][5].keys():
        print(beam.loading.loads[11]["members"][22][n]['x'])
    
    