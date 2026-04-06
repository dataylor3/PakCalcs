import forallpeople as si
si.environment("mystructural", top_level=True)
from math import pi
import re
import json
from typing import Dict, Callable, Optional
import py_loadClasses as lc


class Section:
    def __init__(self, name:str, d:si.Physical, b:si.Physical):
        self.name = name
        self.d = d
        self.b = b

    @property
    def A_c(self):
        return self.b * self.d  # Cross-sectional area for rectangular section

    @property
    def A_t(self):
        return self.b * self.d  # Cross-sectional area for rectangular section

    @property
    def A_s(self):
        return 2/3 * self.b * self.d  # Cross-sectional area for rectangular section

    @property
    def Z_x(self):
        return (self.b*self.d**2)/6  # Section modulus for rectangular section
    
    @property
    def Z_y(self):
        return (self.d*self.b**2)/6  # Section modulus for rectangular section
    

class Material:
    def __init__(self, name:str, f_prime_b:si.Physical, rho_b:float,
                 f_prime_s:si.Physical,
                 f_prime_c:si.Physical, rho_c:float,
                 f_prime_t:si.Physical):
        self.name = name
        self.f_prime_b = f_prime_b  #Characteristic value in bending
        self.rho_b = rho_b          #Material factor for bending
        self.f_prime_s = f_prime_s  #Characteristic value in shear
        self.f_prime_c = f_prime_c  #Characteristic value in compression parallel to grain
        self.rho_c = rho_c          #Material factor for compression
        self.f_prime_t = f_prime_t  #Characteristic value in tension parallel to grain


class Restraints:
    def __init__(self, material:Material, section:Section):
        self.material = material
        self.section = section


class bendRestraints(Restraints):
    def __init__(self, material:Material, section:Section,
                 L_ayT:si.Physical, L_ayB:si.Physical,
                 L_alphaT:si.Physical, L_alphaB:si.Physical):
        super().__init__(material, section)

        self.L_ayT = L_ayT  # Spacing of discrete lateral restraints on the top of the beam
        self.L_ayB = L_ayB  # Spacing of discrete lateral restraints
        self.L_alphaT = L_alphaT  # Spacing of discrete torsional restraints on the top of the beam
        self.L_alphaB = L_alphaB  # Spacing of discrete torsional restraints on

    @property
    def cont_res_limit(self):
        return self.section.d*64*(self.section.b/(self.material.rho_b*self.section.d))**2

    @property
    def top_is_continuous(self):
        return self.L_ayT <= self.cont_res_limit
    @property
    def bottom_is_continuous(self):
        return self.L_ayB <= self.cont_res_limit


class compRestraints(Restraints):
    def __init__(self, material:Material, section:Section,
                 x_cont_res:bool, y_cont_res:bool,
                 L_ax:si.Physical, L_ay:si.Physical,
                 g_13:float, L:si.Physical):
        super().__init__(material, section)

        self.g_13 = g_13  # Strength sharing factor for compression members
        self.L = L        # Length of the member
        self.L_ax = L_ax  # Spacing of discrete restraints in the x direction
        self.L_ay = L_ay  # Spacing of discrete restraints in the y direction
        self.x_cont_res = x_cont_res  # Whether there are continuous restraints in the x direction
        self.y_cont_res = y_cont_res  # Whether there are continuous restraints in the y


class ModificationFactors:
    def __init__(self, k_4:float = 1.0, k_6:float = 1.0, k_9:float = 1.0):
        self.k_4 = k_4  # Moisture content factor    
        self.k_6 = k_6  # Temperature factor
        self.k_9 = k_9  # Strength sharing factor


class beamDesign:
    def __init__(self, section: Section, material: Material,
                 bendrestraints: bendRestraints, mod_factors: ModificationFactors,
                 comprestraints: Optional[compRestraints] = None,
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
        self.rho_b = material.rho_b
        self.rho_c = material.rho_c
        self.bendrestraints = bendrestraints
        self.comprestraints = comprestraints
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
        R = self.bendrestraints

        return self._S1_helper(
            comp_continuous = R.top_is_continuous,
            tens_continuous = R.bottom_is_continuous,

            comp_Lay = R.L_ayT,
            tens_Lay = R.L_ayB,
            tens_Lalpha = R.L_alphaT,   # torsional restraint to compression edge
        )

    @property        
    def S_1Hog(self):
        R = self.bendrestraints

        return self._S1_helper(
            comp_continuous = R.bottom_is_continuous,
            tens_continuous = R.top_is_continuous,

            comp_Lay = R.L_ayB,
            tens_Lay = R.L_ayT,
            tens_Lalpha = R.L_alphaB,   # torsional restraint to compression edge
        )

    def k_12(self, S:float, rho:float):
        #print(f'S_1: {S_1}')
        if rho*S <=10:
            return 1.0
        elif 10<= rho*S <20:
            return 1.5-0.05*(rho*S)
        else:
            return 200/(rho*S)**2

    ### Bending Checks
    def M_d(self, k_1:float, k_12:float, Z:si.Physical):
        return self.phi*k_1*self.k_4*self.k_6*self.k_9*k_12*self.f_prime_b*Z
    
    def checkM_dx(self, k1:float, M_starx:si.Physical):
        if M_starx < 0.0*Nm:
            S_1 = self.S_1Hog
        else:
            S_1 = self.S_1Sag
        k_12 = self.k_12(S_1, self.rho_b)
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
        return M_dx, M_dy, interaction
   
    ### Shear Checks
    def V_d(self, k_1:float):
        return self.phi*k_1*self.k_4*self.k_6*self.f_prime_s*self.section.A_s
    
    def checkV(self, k1:float, V_star:si.Physical):
        V_d = self.V_d(k1)
        UtilRatio = abs(V_star / V_d)
        return V_d, UtilRatio

    ### Tension Checks
    def N_dt(self, k_1:float):
        return self.phi*k_1*self.k_4*self.k_6*self.f_prime_t*self.section.A_t
   
    ### Compressive Checks
    def N_dc(self, k_1:float, k_12:float, A_c:si.Physical):
        return self.phi*k_1*self.k_4*self.k_6*k_12*self.f_prime_c*A_c
    
    def _S_comp_helper(self, axis: str, L_a:si.Physical,
                       col_dim:si.Physical, cont_res:bool):
                       
        d = self.section.d
        b = self.section.b
        L = self.comprestraints.L
        g_13 = self.comprestraints.g_13

        s_n1 = (L_a/col_dim)
        s_n2 = g_13 * L/col_dim
            
        if axis.lower() == 'x':
            s_n3 = 0
        else:
            s_n3 = 3.5 * d/b
        
        if cont_res:
            return min(s_n1, s_n2, s_n3)
        else:
            return min(s_n1, s_n2)
   
    @property
    def S_3(self):
        compR = self.comprestraints
        return self._S_comp_helper(axis='x', L_a=compR.L_ax, col_dim=self.section.d, cont_res=compR.x_cont_res)

    @property
    def S_4(self):
        compR = self.comprestraints
        return self._S_comp_helper(axis='y', L_a=compR.L_ay, col_dim=self.section.b, cont_res=compR.y_cont_res)

    def checkN_d(self, k1:float, N_star:si.Physical):
        if N_star > 0.0*N:
            k_12x = self.k_12(self.S_3, self.rho_c)
            k_12y = self.k_12(self.S_4, self.rho_c)
            N_dx = self.N_dc(k1, k_12x, self.section.A_c)
            N_dy = self.N_dc(k1, k_12y, self.section.A_c)
            UtilRatio_x = abs(N_star / N_dx)
            UtilRatio_y = abs(N_star / N_dy)
            return N_dx, N_dy, UtilRatio_x, UtilRatio_y
        else:
            N_dt = self.N_dt(k1)
            UtilRatio = abs(N_star / N_dt)
            return N_dt, N_dt, UtilRatio, UtilRatio
        
    def checkN_dt(self, k1:float, N_star:si.Physical):
        N_dt = self.N_dt(k1)
        UtilRatio = abs(N_star / N_dt)
        return N_dt, UtilRatio
    
    def check_combined_M_N(self, k1:float, N_star:si.Physical, M_starx:si.Physical, M_stary:si.Physical):
        N_dx, N_dy, _, _ = self.checkN_d(k1, N_star)
        if N_star < 0.0*N:
            N_dt = N_dx
        M_dx, _ = self.checkM_dx(k1, M_starx)
        if M_starx < 0.0*Nm:
            S_1 = self.S_1Hog
        else:
            S_1 = self.S_1Sag
        k12x = self.k_12(S_1, self.rho_b)
        M_dy, _ = self.checkM_dy(k1, M_stary)
        k12y = 1.0
        
        if N_star >= 0.0*N:
            # Interaction equations for combined axial comp and bending
            util1 = (M_starx / M_dx)**2 + abs(N_star / N_dy)
            util2 = abs(M_starx / M_dx) + abs(N_star / N_dx)
            util3 = (M_starx / M_dx)**2 + abs(M_stary / M_dy) + abs(N_star / N_dy)
            util4 = abs(M_starx / M_dx) + (M_stary / M_dy)**2 + abs(N_star / N_dx)
            return M_dx, M_dy, N_dx, N_dy, max(util1, util2, util3, util4)
        else:
            # Interaction equations for combined tension and bending
            util1 = k12x * abs(M_starx / M_dx) + abs(N_star / N_dt)
            util2 = k12y * abs(M_stary / M_dy) + abs(N_star / N_dt)
            util3 = abs(M_starx / M_dx) - self.section.Z_x / self.section.A_t * abs(N_star / M_dx)
            return M_dx, M_dy, N_dt, max(util1, util2, util3)
