from rdkit import Chem
from rdkit.Chem import Descriptors
from matchms import Spectrum
import logging
from matchms.constants import PROTON_MASS
from matchms.filtering.repair_parent_mass_from_smiles.require_parent_mass_match_smiles import \
    _get_monoisotopic_neutral_mass, _mass_diff_within_tolerance
from matchms.filtering.filter_utils.derive_precursor_mz_and_parent_mass import derive_precursor_mz_from_parent_mass
logger = logging.getLogger("matchms")


def repair_parent_mass_is_mol_wt(spectrum_in: Spectrum, mass_tolerance: float):
    """Changes the precursor mz from molecular mass into monoistopic mass

    Manual entered precursor mz is sometimes wrongly added as Molar weight instead of monoisotopic mass
    """
    if spectrum_in is None:
        return None
    spectrum = spectrum_in.clone()
    # Check if parent mass already matches smiles
    if _mass_diff_within_tolerance(spectrum.get("parent_mass"), spectrum.get("smiles"), mass_tolerance):
        return spectrum
    # Check if parent mass matches the smiles mass
    parent_mass = spectrum.get("parent_mass")
    smiles = spectrum.get("smiles")
    smiles_mass = _get_molecular_weight_neutral_mass(smiles)
    mass_difference = parent_mass - smiles_mass
    if abs(mass_difference) < mass_tolerance:
        correct_mass = _get_monoisotopic_neutral_mass(smiles)
        spectrum.set("parent_mass", correct_mass)
        logger.info(f"Parent mass was mol_wt corrected from {parent_mass} to {correct_mass}")
        precursor_mz = derive_precursor_mz_from_parent_mass(spectrum)
        logger.info(f"Precursor mz was derived from parent mass")
        spectrum.set("precursor_mz", precursor_mz)
    return spectrum


def _get_molecular_weight_neutral_mass(smiles):
    mol = Chem.MolFromSmiles(smiles)
    mass = Descriptors.MolWt(mol)
    charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())
    neutral_mass = mass + -charge * PROTON_MASS
    return neutral_mass
