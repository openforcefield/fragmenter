"""
Unit and regression test for the fragmenter package.
"""

# Import package, test suite, and other packages as needed
import fragmenter
from fragmenter import chemi
from cmiles.utils import mol_to_smiles, remove_atom_map
import sys
from fragmenter.tests.utils import using_openeye
import pytest


def test_fragmenter_imported():
    """Sample test, will always pass so long as import statement worked"""
    assert "fragmenter" in sys.modules

@using_openeye
def test_expand_tautomers():
    from openeye import oechem
    imidazol_smiles = 'CC1=CN=CN1'
    oemol = oechem.OEMol()
    oechem.OESmilesToMol(oemol, imidazol_smiles)
    tautomers = fragmenter.fragment._enumerate_tautomers(oemol)
    assert len(tautomers) == 2
    for tau in tautomers:
        assert chemi.get_charge(tau) == 0

    salsalate = 'OC(=O)C1=CC=CC=C1OC(=O)C1=CC=CC=C1O'
    oemol = oechem.OEMol()
    oechem.OESmilesToMol(oemol, salsalate)
    tautomers = fragmenter.fragment._enumerate_tautomers(oemol)
    assert len(tautomers) == 1
    assert chemi.get_charge(tautomers[0]) == -1


@using_openeye
@pytest.mark.parametrize('smiles, forceflip, enum_n, output', [('C1=CN(C=N1)C(C1=CC=CC=C1)C1=CC=C(C=C1)C1=CC=CC=C1', True, False, 2),
                                                      ('C[C@@H](C1=NC(=CS1)C1=CC=C(C=C1)C#N)[C@](O)(CN1C=NC=N1)C1=C(F)C=CC(F)=C1', False, False, 1),
                                                      ('C[C@@H](C1=NC(=CS1)C1=CC=C(C=C1)C#N)[C@](O)(CN1C=NC=N1)C1=C(F)C=CC(F)=C1', True, False, 4),
                                                      ('CN(CC=CC1=CC=CC=C1)CC1=CC=CC2=CC=CC=C12', True, True, 4),
                                                      ('CN(CC=CC1=CC=CC=C1)CC1=CC=CC2=CC=CC=C12', False, False, 2)])
def test_expand_stereoisomers(smiles, forceflip, enum_n, output):
    from openeye import oechem
    oemol = oechem.OEMol()
    oechem.OESmilesToMol(oemol, smiles)
    stereo = fragmenter.fragment._enumerate_stereoisomers(oemol, force_flip=forceflip, enum_nitrogen=enum_n, verbose=False)
    assert len(stereo) == output

@using_openeye
@pytest.mark.parametrize('smiles, tautomers, stereoisomers, max_stereo_return, filter_nitro, output',
                        [('N[C@@H](CC1=CC(I)=C(OC2=CC(I)=C(O)C=C2)C(I)=C1)C(O)=O', True, True, 10, True, 4),
                         ('N[C@@H](CC1=CC(I)=C(OC2=CC(I)=C(O)C=C2)C(I)=C1)C(O)=O', False, False, 10, True, 1),
                         ('N[C@@H](CC1=CC(I)=C(OC2=CC(I)=C(O)C=C2)C(I)=C1)C(O)=O', True, False, 1, True, 2),
                         ('N[C@@H](CC1=CC(I)=C(OC2=CC(I)=C(O)C=C2)C(I)=C1)C(O)=O', False, True, 1, True, 2),
                         ('CC1=C(C(C(=C(N1)C)C(=O)OCC(C)C)c2ccccc2[N+](=O)[O-])C(=O)OC', True, True, 10, True, 2),
                         ('CC1=C(C(C(=C(N1)C)C(=O)OCC(C)C)c2ccccc2[N+](=O)[O-])C(=O)OC', False, False, 1, True, 1),
                         ('CC1=C(C(C(=C(N1)C)C(=O)OCC(C)C)c2ccccc2[N+](=O)[O-])C(=O)OC', True, True, 10, False, 4),
                         ('CC1=C(C(C(=C(N1)C)C(=O)OCC(C)C)c2ccccc2[N+](=O)[O-])C(=O)OC', False, False, 10, False, 2)])
def test_expand_states(smiles, tautomers, stereoisomers, max_stereo_return, filter_nitro, output):
    from openeye import oechem
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    states = fragmenter.fragment.enumerate_states(mol, tautomers=tautomers, stereoisomers=stereoisomers,
                                                  max_stereo_returns=max_stereo_return, filter_nitro=filter_nitro, verbose=False)
    assert len(states) == output

@using_openeye
@pytest.mark.parametrize('smiles, output', [('CCN(CCO)c1ccc(c(c1)C)/N=N/c2ncc(s2)N(=O)=O', True),
                                            ('CC1=C(C(C(=C(N1)C)C(=O)OCC(C)C)c2ccccc2[N+](=O)[O-])C(=O)OC', False)])
def test_filter_nitro(smiles, output):
    from openeye import oechem
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    assert fragmenter.fragment._check_nitro(mol) == output

@using_openeye
def test_keep_track_of_map():
    from openeye import oechem
    smiles = 'c1ccc(cc1)Nc2ncccn2'
    mapped_mol = oechem.OEMol()
    oechem.OESmilesToMol(mapped_mol, smiles)

    frags = fragmenter.fragment.CombinatorialFragmenter(mapped_mol)
    frags.fragment()
    #frags.fragment_all_bonds_not_in_ring_systems()
    #frags.combine_fragments(min_rotors=1, max_rotors=frags.n_rotors+1, restore_maps=True)

    keys = list(frags.fragments.keys())
    assert oechem.OEMolToSmiles(frags.fragments[keys[0]][0]) == '[H:14][c:1]1[c:2]([c:4]([c:9]([c:5]([c:3]1[H:16])[H:18])[NH:13][H:22])[H:17])[H:15]'
    assert oechem.OEMolToSmiles(frags.fragments[keys[1]][0]) == '[H:19][c:6]1[c:7]([n:11][c:10]([n:12][c:8]1[H:21])[NH:13][H:22])[H:20]'


@using_openeye
def test_tag_fgroups():
    from openeye import oechem
    import itertools
    smiles = '[H:40][c:3]1[c:8]([c:20]2[n:30][c:12]([c:14]([n:32]2[n:31][c:11]1[H:48])[C:2]#[C:1][c:13]3[c:9]([c:15]([c:4]([c:5]([c:16]3[C:26]' \
             '([H:58])([H:59])[H:60])[H:42])[H:41])[C:21](=[O:36])[N:35]([H:66])[c:19]4[c:7]([c:6]([c:17]([c:18]([c:10]4[H:47])[C:29]([F:37])([F:38])' \
             '[F:39])[C:28]([H:64])([H:65])[N:34]5[C:24]([C:22]([N:33]([C:23]([C:25]5([H:56])[H:57])([H:52])[H:53])[C:27]([H:61])([H:62])[H:63])([H:50])' \
             '[H:51])([H:54])[H:55])[H:43])[H:44])[H:46])[H:49])[H:45]'
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    frags = fragmenter.fragment.CombinatorialFragmenter(mol)
    fgroups = {}
    fgroups['alkyne_0'] = [1, 2]
    fgroups['carbonyl_0'] = [21, 36]
    fgroups['amide_0'] = [35]
    fgroups['tri_halide_0'] = [29, 37, 38, 39]
    for group in fgroups:
        for i in fgroups[group]:
            a = frags.molecule.GetAtom(oechem.OEHasMapIdx(i))
            assert a.GetData('fgroup') == group
    for group in fgroups:
        atoms = [frags.molecule.GetAtom(oechem.OEHasMapIdx(i)) for i in fgroups[group]]
        for atom in itertools.combinations(atoms, 2):
            # Check for bond
            b = frags.molecule.GetBond(atom[0], atom[1])
            if b:
                assert b.GetData('fgroup') == group

@using_openeye
def test_rotor_wbo():
    from openeye import oechem
    smiles ='[H:5][C:1]([H:6])([H:7])[C:3]([H:11])([H:12])[C:4]([H:13])([H:14])[C:2]([H:8])([H:9])[H:10]'
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    assert f.rotors_wbo == {}
    f._get_rotor_wbo()
    assert list(f.rotors_wbo.keys()) == [(3, 4)]
    assert round(f.rotors_wbo[(3, 4)], ndigits=3) ==  0.986


@using_openeye
def test_get_bond():
    from openeye import oechem
    smiles ='[H:5][C:1]([H:6])([H:7])[C:3]([H:11])([H:12])[C:4]([H:13])([H:14])[C:2]([H:8])([H:9])[H:10]'
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    bond = f.get_bond(bond_tuple=(3, 4))
    assert bond.IsRotor()

def test_build_fragment():
    from openeye import oechem
    smiles = 'CCCCCC'
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.calculate_wbo()
    f._get_rotor_wbo()
    setattr(f, 'threshold', 0.05)
    for bond in f.rotors_wbo:
        f.build_fragment(bond)
    assert len(f.fragments) == 3
    for bond in f.fragments:
        remove_atom_map(f.fragments[bond])
        assert oechem.OEMolToSmiles(f.fragments[bond]) == 'CCCC'


@using_openeye
def test_build_WBOfragment():
    """ Test build fragment"""
    from openeye import oechem
    smiles = 'CCCCC'
    mol = chemi.smiles_to_oemol(smiles)
    oechem.OESmilesToMol(mol, smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.fragment()
    assert len(f.fragments) == len(f.rotors_wbo)
    assert f.fragments.keys() == f.rotors_wbo.keys()


def test_to_atom_bond_set():
    from openeye import oechem
    smiles = '[H:38][c:1]1[c:2]([c:14]([n:28][c:5]([c:8]1[C:25]([H:64])([H:65])[N:33]2[C:17]([C:19]([N:34]([C:20]([C:18]2([H:46])[H:47])([H:50])[H:51])[C:26]([H:66])([H:67])[C:22]([H:55])([H:56])[H:57])([H:48])[H:49])([H:44])[H:45])[H:42])[N:35]([H:69])[c:16]3[n:29][c:6]([c:12]([c:13]([n:31]3)[c:7]4[c:3]([c:10]5[c:9]([c:11]([c:4]4[H:41])[F:36])[n:30][c:15]([n:32]5[C:27]([H:68])([C:23]([H:58])([H:59])[H:60])[C:24]([H:61])([H:62])[H:63])[C:21]([H:52])([H:53])[H:54])[H:40])[F:37])[H:43])[H:39]'
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    f = fragmenter.fragment.Fragmenter(mol)
    atoms = {17, 18, 19, 20, 22, 26, 33, 34, 66, 67}
    bonds = {(17, 19), (17, 33), (18, 20), (18, 33), (19, 34), (20, 34), (22, 26), (26, 34),  (26, 66), (26, 67)}
    atom_bond_set = f._to_atom_bond_set(atoms=atoms, bonds=bonds)
    atoms_2 = set([a.GetMapIdx() for a in atom_bond_set.GetAtoms()])
    assert atoms == atoms_2
    bonds_2 = set()
    for b in atom_bond_set.GetBonds():
        a1 = b.GetBgn().GetMapIdx()
        a2 = b.GetEnd().GetMapIdx()
        bonds_2.add(tuple(sorted((a1, a2))))
    assert bonds == bonds_2

def test_atom_bond_set_to_mol():
    from openeye import oechem
    smiles = '[H:38][c:1]1[c:2]([c:14]([n:28][c:5]([c:8]1[C:25]([H:64])([H:65])[N:33]2[C:17]([C:19]([N:34]([C:20]([C:18]2([H:46])[H:47])([H:50])[H:51])[C:26]([H:66])([H:67])[C:22]([H:55])([H:56])[H:57])([H:48])[H:49])([H:44])[H:45])[H:42])[N:35]([H:69])[c:16]3[n:29][c:6]([c:12]([c:13]([n:31]3)[c:7]4[c:3]([c:10]5[c:9]([c:11]([c:4]4[H:41])[F:36])[n:30][c:15]([n:32]5[C:27]([H:68])([C:23]([H:58])([H:59])[H:60])[C:24]([H:61])([H:62])[H:63])[C:21]([H:52])([H:53])[H:54])[H:40])[F:37])[H:43])[H:39]'
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    f = fragmenter.fragment.Fragmenter(mol)
    atoms = {17, 18, 19, 20, 22, 26, 33, 34, 66, 67}
    bonds = {(17, 19), (17, 33), (18, 20), (18, 33), (19, 34), (20, 34), (22, 26), (26, 34),  (26, 66), (26, 67)}
    atom_bond_set = f._to_atom_bond_set(atoms=atoms, bonds=bonds)
    mol = f._atom_bond_set_to_mol(atom_bond_set)
    for b in mol.GetBonds():
        a1 = b.GetBgn()
        a2 = b.GetEnd()
        if not a1.IsHydrogen() and not a2.IsHydrogen():
            assert tuple(sorted((a1.GetMapIdx(), a2.GetMapIdx()))) in bonds

def test_calculate_wbo():
    smiles = 'CCCC'
    oemol = chemi.smiles_to_oemol(smiles, name='butane')
    f = fragmenter.fragment.WBOFragmenter(oemol)
    mol = f.calculate_wbo()
    assert not mol
    for bond in f.molecule.GetBonds():
        assert 'WibergBondOrder' in bond.GetData()

    mol = f.calculate_wbo(f.molecule)
    assert mol
    for bond in mol.GetBonds():
        assert 'WibergBondOrder' in bond.GetData()

def test_compare_wbo():
    from openeye import oechem
    smiles ='[H:5][C:1]([H:6])([H:7])[C:3]([H:11])([H:12])[C:4]([H:13])([H:14])[C:2]([H:8])([H:9])[H:10]'
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.calculate_wbo()
    f._get_rotor_wbo()
    assert f.compare_wbo(fragment=mol, bond_tuple=(3, 4)) == 0.0

@pytest.mark.parametrize('input, output', [('CCCC', 0),
                                           ('c1ccccc1', 1),
                                           ('c1ccccc1C', 1)])

def test_find_ring_systems(input, output):
    mol = chemi.smiles_to_oemol(input)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f._find_ring_systems()
    assert len(f.ring_systems) == output

@pytest.mark.parametrize('input, output', [(True, 7),
                                           (False, 6)])
def test_keep_non_rotor(input, output):
    mol = chemi.smiles_to_oemol('c1ccccc1C')
    f = fragmenter.fragment.WBOFragmenter(mol)
    f._find_ring_systems(keep_non_rotor_ring_substituents=input)
    assert len(f.ring_systems[1][0]) == output

def test_find_ortho_substituent():
    from openeye import oechem
    smiles ="[H:34][c:1]1[c:2]([c:6]([c:7]([c:8]([c:3]1[H:36])[Cl:33])[N:28]([H:57])[C:14](=[O:30])[c:9]2[c:5]([n:23][c:13]([s:32]2)[N:29]([H:58])[c:11]3[c:4]([c:10]([n:24][c:12]([n:25]3)[C:20]([H:50])([H:51])[H:52])[N:26]4[C:15]([C:17]([N:27]([C:18]([C:16]4([H:41])[H:42])([H:45])[H:46])[C:21]([H:53])([H:54])[C:22]([H:55])([H:56])[O:31][H:59])([H:43])[H:44])([H:39])[H:40])[H:37])[H:38])[C:19]([H:47])([H:48])[H:49])[H:35]"
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f._find_ring_systems(keep_non_rotor_ring_substituents=False)
    ortho = f._find_ortho_substituent(ring_idx=1, rot_bond=(7, 28))
    assert len(ortho[0]) == 2
    assert len(ortho[1]) == 2
    assert ortho[0] == set((19, 33))
    assert ortho[1] == set(((19, 6), (33, 8)))

def test_find_rotatable_bonds():
    from openeye import oechem
    smiles = '[H:38][c:1]1[c:2]([c:14]([n:28][c:5]([c:8]1[C:25]([H:64])([H:65])[N:33]2[C:17]([C:19]([N:34]([C:20]([C:18]2([H:46])[H:47])([H:50])[H:51])[C:26]([H:66])([H:67])[C:22]([H:55])([H:56])[H:57])([H:48])[H:49])([H:44])[H:45])[H:42])[N:35]([H:69])[c:16]3[n:29][c:6]([c:12]([c:13]([n:31]3)[c:7]4[c:3]([c:10]5[c:9]([c:11]([c:4]4[H:41])[F:36])[n:30][c:15]([n:32]5[C:27]([H:68])([C:23]([H:58])([H:59])[H:60])[C:24]([H:61])([H:62])[H:63])[C:21]([H:52])([H:53])[H:54])[H:40])[F:37])[H:43])[H:39]'
    mol = oechem.OEMol()
    oechem.OESmilesToMol(mol, smiles)
    # Add map
    f = fragmenter.fragment.WBOFragmenter(mol)
    rot_bonds = f._find_rotatable_bonds()
    assert len(rot_bonds) == 7
    expected_rot_bonds = [(14, 35), (8, 25), (25, 33), (26, 34), (16, 35), (7, 13), (27, 32)]
    for bond in rot_bonds:
        assert bond in expected_rot_bonds

def test_add_substituent():
    smiles = 'CCCCCC'
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.fragment()
    for bond in f.fragments:
        assert mol_to_smiles(f.fragments[bond], mapped=False, explicit_hydrogen=False) == 'CCCC'

    mol = f.fragments[(3, 5)]
    atoms = set()
    bonds = set()
    for a in mol.GetAtoms():
        if a.IsHydrogen():
            continue
        atoms.add(a.GetMapIdx())
    for b in mol.GetBonds():
        a1 = b.GetBgn()
        a2 = b.GetEnd()
        if a1.IsHydrogen() or a2.IsHydrogen():
            continue
        bonds.add((a1.GetMapIdx(), a2.GetMapIdx()))

    mol = f._add_next_substituent(atoms, bonds, target_bond=(3, 5))

    assert mol_to_smiles(mol, mapped=False, explicit_hydrogen=False) == 'CCCCC'

def test_to_json():
    smiles = 'CCCCCC'
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.fragment()
    json_dict = f.to_json()
    assert len(json_dict) == 1
    assert list(json_dict.keys())[0] == 'CCCC'
    assert 'provenance' in json_dict['CCCC']
    assert 'cmiles_identifiers' in json_dict['CCCC']

def test_to_qcscheme_mol():
    smiles = 'CCCCCC'
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.fragment()

    qcschema_mol = f._to_qcschema_mol(f.fragments[(3, 5)])
    assert 'initial_molecule' in qcschema_mol
    assert 'geometry' in qcschema_mol['initial_molecule'][0]
    assert 'symbols' in qcschema_mol['initial_molecule'][0]
    assert 'connectivity' in qcschema_mol['initial_molecule'][0]
    assert 'identifiers' in qcschema_mol
    assert 'provenance' in qcschema_mol

def test_to_qcschema_mols():
    smiles = 'CCCCCC'
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.fragment()

    qcschema_mol = f.to_qcschema_mols()
    assert len(qcschema_mol) == 1

def test_td_inputs():
    smiles = 'CCCCCC'
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f.fragment()

    td_inputs = f.to_torsiondrive_json()
    assert len(td_inputs) == 1

@pytest.mark.parametrize('smiles, output',
                        [('OC1(CN(C1)C(=O)C1=C(NC2=C(F)C=C(I)C=C2)C(F)=C(F)C=C1)[C@@H]1CCCCN1', {20: 'S'}),
                         ('OC1(CN(C1)C(=O)C1=C(NC2=C(F)C=C(I)C=C2)C(F)=C(F)C=C1)[C@H]1CCCCN1', {20: 'R'}),
                         ('C\C=C\C', {(1, 2): 'E'}),
                         ('C/C=C\C', {(1, 2): 'Z'})])
def test_find_stereo(smiles, output):
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f._find_stereo()
    assert f.stereo == output

@pytest.mark.parametrize('smiles, frag, output',
                        [('C[C@@](F)(Cl)I','C[C@@](F)(Cl)I', True ),
                         ('C[C@@](F)(Cl)I','C[C@](F)(Cl)I',  False),
                         ('C\C=C\C', 'C\C=C\C', True),
                         ('C/C=C\C', 'C\C=C\C', False)])

def test_check_stereo(smiles, frag, output):
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f._find_stereo()
    frag = chemi.smiles_to_oemol(frag, add_atom_map=True)
    assert f._check_stereo(frag) == output


@pytest.mark.parametrize('smiles, frag',
                        [('C[C@@](F)(Cl)I','C[C@@](F)(Cl)I'),
                         ('C[C@@](F)(Cl)I','C[C@](F)(Cl)I'),
                         ('C\C=C\C', 'C\C=C\C'),
                         ('C/C=C\C', 'C\C=C\C')])
def tet_fix_stereo(smiles, frag):
    mol = chemi.smiles_to_oemol(smiles)
    f = fragmenter.fragment.WBOFragmenter(mol)
    f._find_stereo()
    frag = chemi.smiles_to_oemol(frag, add_atom_map=True)
    fixed = f._fix_stereo(frag)
    assert f._check_stereo(fixed) == True

@pytest.mark.parametrize('engine', ['WBO', 'combinatorial'])
def test_depict_fragments(engine):
    mol = chemi.smiles_to_oemol('CCCCC')
    if engine == 'WBO':
        f = fragmenter.fragment.WBOFragmenter(mol)
    if engine =='combinatorial':
        f = fragmenter.fragment.CombinatorialFragmenter(mol)
    f.fragment()
    assert f.depict_fragments('test.pdf') == True