# Zeolite Structure Files (CIF)

This directory contains crystal structure files for zeolites in CIF (Crystallographic Information File) format.

## Included Structures

- **MOR.cif** - Mordenite zeolite structure

## How to Add More Structures

### From IZA Database

The IZA (International Zeolite Association) database provides standard zeolite structures:

```bash
# Download a specific zeolite (replace XXX with the 3-letter code)
wget https://europe.iza-structure.org/IZA-SC/cif/XXX.cif -O cifs/XXX.cif

# Common zeolites:
wget https://europe.iza-structure.org/IZA-SC/cif/MFI.cif -O cifs/MFI.cif  # ZSM-5
wget https://europe.iza-structure.org/IZA-SC/cif/LTA.cif -O cifs/LTA.cif  # Zeolite A
wget https://europe.iza-structure.org/IZA-SC/cif/FAU.cif -O cifs/FAU.cif  # Zeolite Y
wget https://europe.iza-structure.org/IZA-SC/cif/CHA.cif -O cifs/CHA.cif  # Chabazite
```

### From Other Sources

- **CoRE MOF Database**: https://gregchung.github.io/CoRE-MOFs/
- **Cambridge Structural Database (CSD)**: https://www.ccdc.cam.ac.uk/
- **Materials Project**: https://materialsproject.org/

## Structure Naming

The StructureExpert agent searches for structures by name. Use standard 3-letter IZA codes (e.g., MOR, MFI, LTA) for zeolites.

For custom structures, ensure the filename matches the structure name you'll use in simulation requests.

## References

- IZA Structure Commission: http://www.iza-structure.org/
- Database of Zeolite Structures: http://www.iza-structure.org/databases/
