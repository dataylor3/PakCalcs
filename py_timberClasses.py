import forallpeople as si
si.environment("mystructural", top_level=True)
from math import pi
import re
import json
from typing import Dict, Callable, Optional
import py_loadClasses as lc

class Section:
    def __init__(self, name:str, d:si.Physical, b:si.Physical, rho_b:float):
        self.name = name
        self.d = d
        self.b = b
        self.rho_b = rho_b

    @property
    def A_s(self):
        return 2/3 * self.b * self.d  # Cross-sectional area for rectangular section

    @property
    def Z_x(self):
        return (self.b*self.d**2)/6  # Section modulus for rectangular section
    
    @property
    def Z_y(self):
        return (self.d*self.b**2)/6  # Section modulus for rectangular section
    
    @property
    def cont_res_limit(self):
        return self.d*64*(self.b/(self.rho_b*self.d))**2


class Restraints:
    def __init__(self, L_ayT:si.Physical, L_ayB:si.Physical, L_alphaT:si.Physical, L_alphaB:si.Physical, cont_res_limit:si.Physical):
        self.L_ayT = L_ayT
        self.L_ayB = L_ayB
        self.L_alphaT = L_alphaT
        self.L_alphaB = L_alphaB
        self.cont_res_limit = cont_res_limit

    @property
    def top_is_continuous(self):
        return self.L_ayT <= self.cont_res_limit
    @property
    def bottom_is_continuous(self):
        return self.L_ayB <= self.cont_res_limit


class Material:
    def __init__(self, name:str, f_prime_b:si.Physical,
                 f_prime_s:si.Physical,
                 f_prime_c:si.Physical,
                 f_prime_t:si.Physical):
        self.name = name
        self.f_prime_b = f_prime_b  #Characteristic value in bending
        self.f_prime_s = f_prime_s  #Characteristic value in shear
        self.f_prime_c = f_prime_c  #Characteristic value in compression parallel to grain
        self.f_prime_t = f_prime_t  #Characteristic value in tension parallel to grain


class ModificationFactors:
    def __init__(self, k_4:float = 1.0, k_6:float = 1.0, k_9:float = 1.0):
        self.k_4 = k_4  # Moisture content factor    
        self.k_6 = k_6  # Temperature factor
        self.k_9 = k_9  # Strength sharing factor


class beamDesign:
    def __init__(self, section: Section, restraints: Restraints,
                   material: Material, mod_factors: ModificationFactors,
                      phi:float = 0.95 ):
        """
        Parameters
        section: The cross-sectional properties of the beam
        restraints: The lateral and torsional restraints of the beam
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
        self.section = section
        self.rho_b = section.rho_b
        self.restraints = restraints
        self.f_prime_b = material.f_prime_b
        self.f_prime_s = material.f_prime_s
        self.f_prime_c = material.f_prime_c
        self.f_prime_t = material.f_prime_t
        self.k_4 = mod_factors.k_4
        self.k_6 = mod_factors.k_6
        self.k_9 = mod_factors.k_9
    
    
    def _S1_helper(self,
                comp_continuous, tens_continuous,
                comp_Lay, tens_Lay, tens_Lalpha):
        d = self.section.d
        b = self.section.b

        # --- Compression flange ---
        if comp_continuous:
            S_comp = 0.0
        else:
            S_comp = 1.25 * (d/b) * (comp_Lay/d)**0.5

        # --- Tension flange ---
        if tens_continuous:
            S_t1 = 2.25 * d/b
            S_t2 = 1.5 * d/b / ((pi*d/tens_Lalpha)**2 + 0.4)**0.5
            S_tens = min(S_t1, S_t2)
        else:
            S_tens = (d/b)**1.35 * (tens_Lay/d)**0.25

        return min(S_comp, S_tens)

    @property
    def S_1Sag(self):
        R = self.restraints

        return self._S1_helper(
            comp_continuous = R.top_is_continuous,
            tens_continuous = R.bottom_is_continuous,

            comp_Lay = R.L_ayT,
            tens_Lay = R.L_ayB,
            tens_Lalpha = R.L_alphaT,   # torsional restraint to compression edge
        )

    @property        
    def S_1Hog(self):
        R = self.restraints

        return self._S1_helper(
            comp_continuous = R.bottom_is_continuous,
            tens_continuous = R.top_is_continuous,

            comp_Lay = R.L_ayB,
            tens_Lay = R.L_ayT,
            tens_Lalpha = R.L_alphaB,   # torsional restraint to compression edge
        )

    def k_12(self, S_1:float):
        #print(f'S_1: {S_1}')
        if self.rho_b*S_1 <=10:
            return 1.0
        elif 10<= self.rho_b*S_1 <20:
            return 1.5-0.05*(self.rho_b*S_1)
        else:
            return 200/(self.rho_b*S_1)**2
    ### Bending Checks
    def M_d(self, k_1:float, k_12:float, Z:si.Physical):
        return self.phi*k_1*self.k_4*self.k_6*self.k_9*k_12*self.f_prime_b*Z
    
    def checkM_dx(self, k1:float, M_starx:si.Physical):
        if M_starx < 0.0*Nm:
            S_1 = self.S_1Hog
        else:
            S_1 = self.S_1Sag
        k_12 = self.k_12(S_1)
        M_dx = self.M_d(k1, k_12, self.section.Z_x)
        #print(type(M_dx), M_dx, type(M_starx), M_starx)
        UtilRatio = abs(M_starx / M_dx)
        return M_dx, UtilRatio

    def checkM_dy(self, k1:float, M_stary:si.Physical):
        k_12 = 1.0
        M_dy = self.M_d(k1, k_12, self.section.Z_y)
        UtilRatio = abs(M_stary / M_dy)
        return M_dy, UtilRatio

    def check_combined_Mx_My(self, k1:float, M_starx:si.Physical, M_stary:si.Physical):
        M_dx, Util_x = self.checkM_dx(k1, M_starx)
        M_dy, Util_y = self.checkM_dy(k1, M_stary)

        # Interaction equation for combined bending
        interaction = abs(M_starx / M_dx) + abs(M_stary / M_dy)
        return interaction
   
    ### Shear Checks
    def V_d(self, k_1:float):
        return self.phi*k_1*self.k_4*self.k_6*self.f_prime_s*self.section.A_s
    
    def checkV(self, k1:float, V_star:si.Physical):
        V_d = self.V_d(k1)
        UtilRatio = abs(V_star / V_d)
        return V_d, UtilRatio

