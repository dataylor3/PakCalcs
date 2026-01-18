
import math
import pytest

# Import the class and the forallpeople environment from the module under test
import timberClasses as tc

# Ensure units are available (module sets environment to 'mystructural')
si = tc.si

# Helper to build a beam with convenient defaults, letting each test override as needed

def make_beam(
    d: si.Physical=300*mm,
    b=45*mm,
    L=10*m,
    L_ayT=0.3*m,
    L_ayB=3*m,
    L_aphaT=6*m,
    L_aphaB=6*m,
    rho_b=0.81,
):
    return tc.beamDesign(
        d=d, b=b, L=L,
        L_ayT=L_ayT, L_ayB=L_ayB,
        L_aphaT=L_aphaT, L_aphaB=L_aphaB,
        rho_b=rho_b, f_prime_b=19*MPa
    )


def test_example_values_match_properties():
    beam = make_beam()
    # Calculate expected S1Sag and S1Hog using the same formulas for an oracle check
    # Copy of logic from timberClasses to make the expected values explicit
    cont_res_limit = beam.d*64*((beam.b/(beam.rho_b*beam.d))**2)

    # --- S1Sag ---
    if beam.L_ayT <= cont_res_limit:
        s_top_sag = 0
    else:
        s_top_sag = 1.25*(beam.d/beam.b)*((beam.L_ayT/beam.d)**0.5)

    if beam.L_ayB <= cont_res_limit:
        s_bottom_sag = 2.25*beam.d/beam.b
    else:
        s_bottom1_sag = (beam.d/beam.b)**1.35*((beam.L_ayT/beam.d)**0.25)
        s_bottom2_sag = 1.5*beam.d/beam.b/(((math.pi*beam.d/beam.L_aphaT)**2)+0.4)**0.5
        s_bottom_sag = min(s_bottom1_sag, s_bottom2_sag)

    expected_S1Sag = min(s_top_sag, s_bottom_sag)

    # --- S1Hog ---
    if beam.L_ayT <= cont_res_limit:
        s_top_hog = 2.25*beam.d/beam.b
    else:
        s_top1_hog = (beam.d/beam.b)**1.35*((beam.L_ayT/beam.d)**0.25)
        s_top2_hog = 1.5*beam.d/beam.b/(((math.pi*beam.d/beam.L_aphaB)**2)+0.4)**0.5
        s_top_hog = min(s_top1_hog, s_top2_hog)

    if beam.L_ayB <= cont_res_limit:
        s_bottom_hog = 0
    else:
        s_bottom_hog = 1.25*(beam.d/beam.b)*((beam.L_ayB/beam.d)**0.5)

    expected_S1Hog = min(s_top_hog, s_bottom_hog)

    assert pytest.approx(expected_S1Sag) == beam.S_1Sag
    assert pytest.approx(expected_S1Hog) == beam.S_1Hog

    # Check k12 values computed via piecewise function
    def k12_expected(S1):
        val = beam.rho_b * S1
        if val <= 10:
            return 1.0
        elif 10 <= val < 20:
            return 1.5 - 0.05*val
        else:
            return (200/(val**2))

    assert pytest.approx(k12_expected(expected_S1Sag)) == beam.k_12Sag
    assert pytest.approx(k12_expected(expected_S1Hog)) == beam.k_12Hog


def test_k12_piecewise_regions():
    # Create inputs so that rho_b * S1 lands in each branch:
    #   - <= 10  -> k12 = 1.0
    #   - 10..20 -> k12 = 1.5 - 0.05*(rho_b*S1)
    #   - >= 20  -> k12 = 200 / (rho_b*S1)^2
    # We control S1 via restraint spacings and b/d ratios.

    # Base geometry
    d = 400*mm
    b = 40*mm
    rho = 1.0

    # Region 1: small S1 -> top/bottom fully restrained (make L_ayT/B tiny)
    beam1 = make_beam(d=d, b=b, L_ayT=1*mm, L_ayB=1*mm, L_aphaT=10*m, L_aphaB=10*m, rho_b=rho)
    assert beam1.rho_b * beam1.S_1Sag <= 10
    assert beam1.k_12Sag == pytest.approx(1.0)
    assert beam1.rho_b * beam1.S_1Hog <= 10
    assert beam1.k_12Hog == pytest.approx(1.0)

    # Region 2: mid S1 -> tune L_ayT so S1 ~ 12–18
    beam2 = make_beam(d=d, b=b, L_ayT=10*m, L_ayB=10*m, L_aphaT=1*m, L_aphaB=1*m, rho_b=rho)
    val_sag = beam2.rho_b * beam2.S_1Sag
    val_hog = beam2.rho_b * beam2.S_1Hog
    assert 10 <= val_sag < 20
    assert 10 <= val_hog < 20
    expected2_sag = 1.5 - 0.05*val_sag
    expected2_hog = 1.5 - 0.05*val_hog
    assert beam2.k_12Sag == pytest.approx(expected2_sag)
    assert beam2.k_12Hog == pytest.approx(expected2_hog)

    # Region 3: large S1 -> weak lateral restraint and small torsional restraint
    beam3 = make_beam(d=d, b=b, L_ayT=10*m, L_ayB=10*m, L_aphaT=10*m, L_aphaB=10*m, rho_b=rho)
    val_sag3 = beam3.rho_b * beam3.S_1Sag
    val_hog3 = beam3.rho_b * beam3.S_1Hog
    assert val_sag3 >= 20
    assert val_hog3 >= 20
    expected3_sag = 200/(val_sag3**2)
    expected3_hog = 200/(val_hog3**2)
    assert beam3.k_12Sag == pytest.approx(expected3_sag)
    assert beam3.k_12Hog == pytest.approx(expected3_hog)


def test_monotonicity_wrt_restraint_spacing():
    # As restraint spacing increases, slenderness effect S1 should not decrease.
    beam_a = make_beam(L_ayT=0.2*m, L_ayB=0.2*m)
    beam_b = make_beam(L_ayT=2.0*m, L_ayB=2.0*m)
    assert beam_b.S_1Sag >= beam_a.S_1Sag
    assert beam_b.S_1Hog >= beam_a.S_1Hog

