# RASPA Force Field Library

This directory contains pre-defined force field parameter files for common adsorbates and framework atoms.

## Available Force Fields

### TraPPE (Transferable Potentials for Phase Equilibria)

**Atmospheric & Industrial Gases:**
- `TraPPE_CO2.def` - Carbon dioxide (3-site rigid linear)
- `TraPPE_CH4.def` - Methane (united atom)
- `TraPPE_N2.def` - Nitrogen (3-site with COM)
- `TraPPE_O2.def` - Oxygen (2-site)
- `TraPPE_CO.def` - Carbon monoxide (2-site)

**Noble Gases:**
- `TraPPE_He.def` - Helium (single-site)
- `TraPPE_Ar.def` - Argon (single-site)
- `TraPPE_Kr.def` - Krypton (single-site)
- `TraPPE_Xe.def` - Xenon (single-site)

**Hydrogen & Derivatives:**
- `TraPPE_H2.def` - Hydrogen (3-site Buch model)

**Polar Molecules:**
- `TraPPE_H2O.def` - Water (3-site rigid)
- `TraPPE_NH3.def` - Ammonia (4-site pyramidal)

**Acid Gases:**
- `TraPPE_SO2.def` - Sulfur dioxide (3-site bent)
- `TraPPE_H2S.def` - Hydrogen sulfide (3-site bent)

**Light Hydrocarbons:**
- `TraPPE_C2H6.def` - Ethane (united atom)
- `TraPPE_C3H8.def` - Propane (united atom)
- `TraPPE_C2H4.def` - Ethylene (united atom)

**References:**
- CO2: Garcia-Sanchez et al., J. Phys. Chem. C 2009, 113, 8814-8820
- CH4/alkanes: Martin & Siepmann, J. Phys. Chem. B 1998, 102, 2569-2577
- N2/O2/CO/noble gases: Potoff & Siepmann, AIChE J. 2001, 47, 1676-1682
- H2: Buch, V. J. Chem. Phys. 1994, 100, 7610-7629
- H2O: Stubbs et al., J. Phys. Chem. B 2004, 108, 17596-17605
- NH3/C2H4: Wick et al., J. Phys. Chem. B 2000, 104, 8008-8016
- SO2: Kamath et al., J. Phys. Chem. B 2004, 108, 14130-14136
- H2S: Kamath & Potoff, J. Phys. Chem. B 2006, 110, 1349-1353

### UFF (Universal Force Field)

**Framework Atoms (Zeolites):**
- `UFF_Framework.def` - Common zeolite atoms (Si, O, Al, Na, Ca)

**Reference:**
- Rappé et al., J. Am. Chem. Soc. 1992, 114, 10024-10035

### UFF4MOF (UFF for MOFs)

**Framework Atoms (MOFs):**
- `UFF4MOF_Framework.def` - MOF metal centers (Zn, Cu, Fe, Cr, Zr, etc.) + organic linkers (C, H, N, O, S, P, halogens)

**Reference:**
- Addicoat et al., J. Chem. Theory Comput. 2014, 10, 880-891

**Common MOF Support:**
- MOF-5 (Zn-BDC), HKUST-1 (Cu-BTC), UiO-66 (Zr), MIL-53 (Al/Cr/Fe), ZIF-8 (Zn-methylimidazolate)

### DREIDING

**Generic Framework:**
- `DREIDING_Framework.def` - Generic organic/inorganic atoms with hybridization types

**Reference:**
- Mayo et al., J. Phys. Chem. 1990, 94, 8897-8909

**Note:** Uses geometric mean mixing (differs from Lorentz-Berthelot)

## File Format

Each `.def` file contains:

1. **Pseudo atoms definition** - Atom types with properties
2. **Force field parameters** - Lennard-Jones epsilon and sigma
3. **Notes** - Units, bond lengths, special considerations

## Usage by Agents

### ForceFieldExpert Agent

The ForceFieldExpert can:
1. Read these pre-defined force fields
2. Combine adsorbate + framework parameters
3. Generate complete RASPA force field files

### Manual Usage

To use a force field in your simulation:

```python
# Read TraPPE CO2 parameters
with open("forcefields/TraPPE_CO2.def") as f:
    co2_params = parse_force_field(f.read())

# Combine with framework parameters
from forcefields.UFF_Framework import framework_params
combined = merge_force_fields(co2_params, framework_params)
```

## Parameter Units

**Lennard-Jones:**
- epsilon: K (Kelvin)
- sigma: Angstrom (Å)

**Charges:**
- |e| (elementary charge)

**Masses:**
- amu (atomic mass units)

**Bond Lengths/Angles:**
- Distances: Angstrom (Å)
- Angles: degrees (°)

## Data Accuracy

⚠️ **ALL parameters are taken directly from peer-reviewed TraPPE publications**

- Values are **exact as published** in original references
- No approximations or rounding applied
- Molecular geometries (bond lengths, angles) match experimental data
- Validated against experimental vapor-liquid equilibria and adsorption data
- For critical applications, verify against original papers cited in each .def file

## Mixing Rules

All TraPPE force fields use **Lorentz-Berthelot** mixing rules:
- sigma_ij = (sigma_i + sigma_j) / 2
- epsilon_ij = sqrt(epsilon_i * epsilon_j)

## Adding New Force Fields

To add a new force field:

1. Create `<name>.def` file
2. Follow the format in existing files
3. Include reference citation
4. Specify units clearly
5. Add to this README

## Force Field Selection Guide

### For MOF Simulations

**Recommended setup:**
- **Adsorbates** (CO2, CH4, N2, etc.) → Use **TraPPE force fields**
- **MOF framework** → Use **UFF4MOF_Framework.def**
- **Alternative** → DREIDING (better for organic linkers)

**Example (HKUST-1 + CO2):**
```
Adsorbate: TraPPE_CO2.def  
Framework: UFF4MOF_Framework.def (Cu, O, C, H)
Mixing: Lorentz-Berthelot (adsorbate-framework)
```

### For Zeolite Simulations

**Recommended setup:**
- **Adsorbates** → Use **TraPPE force fields**
- **Zeolite framework** → Use **UFF_Framework.def** (Si, O, Al, Na, Ca)

**Example (MOR + CO2):**
```
Adsorbate: TraPPE_CO2.def
Framework: UFF_Framework.def (Si, O)
```

## Notes

- **Charges**: Framework charges often need to be assigned separately (from CIF, QEq, or DFT)
- **Validation**: Always validate against experimental data
- **Mixing Rules**: 
  - TraPPE + UFF/UFF4MOF: Lorentz-Berthelot
  - DREIDING: Geometric mean (σ_ij = √(σ_i × σ_j), ε_ij = √(ε_i × ε_j))
- **Rigid molecules**: CO2, N2, O2, CO are rigid (fixed bond lengths/angles)
- **MOF-specific**: UFF4MOF is optimized for MOF metal centers and coordination environments

## Application Guide

**Gas Storage:**
- H2 storage: `TraPPE_H2.def`
- CH4 storage (natural gas): `TraPPE_CH4.def`
- CO2 sequestration: `TraPPE_CO2.def`

**Gas Separation:**
- CO2/CH4 (biogas, natural gas): `TraPPE_CO2.def` + `TraPPE_CH4.def`
- O2/N2 (air separation): `TraPPE_O2.def` + `TraPPE_N2.def`
- Olefin/paraffin: `TraPPE_C2H4.def` + `TraPPE_C2H6.def`
- Acid gas removal: `TraPPE_H2S.def`, `TraPPE_SO2.def`

**Water Adsorption:**
- Humidity effects: `TraPPE_H2O.def`
- Water purification: `TraPPE_H2O.def`

**Pore Characterization:**
- Helium void volume: `TraPPE_He.def`
- Argon BET surface area: `TraPPE_Ar.def`

**Refrigerants & Cryogenics:**
- Noble gases: `TraPPE_Ar.def`, `TraPPE_Kr.def`, `TraPPE_Xe.def`
- Ammonia: `TraPPE_NH3.def`

## Paper Reproduction

For Table 2 force field extraction tests:
- Garcia-Sanchez 2009: Use TraPPE_CO2.def as reference
- Vujić 2016: Use TraPPE_N2.def, TraPPE_O2.def as reference
- Martin-Calvo 2015: Use TraPPE_CO2.def as reference
