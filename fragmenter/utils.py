import os
from typing import Dict

import yaml
from pkg_resources import resource_filename


def get_fgroup_smarts() -> Dict[str, str]:
    """Returns a dictionary containing the SMARTS representations of different
    functional groups loaded from the internal ``fgroup_smarts.yml`` file.

    Returns
    -------
        A dictionary where each key is the name of a functional group and each value
        the corresponding SMARTS pattern.
    """

    file_name = resource_filename(
        "fragmenter", os.path.join("data", "fgroup_smarts.yml")
    )

    with open(file_name, "r") as file:
        functional_groups = yaml.safe_load(file)

    return functional_groups


def get_fgroup_smarts_comb() -> Dict[str, str]:
    """Returns a dictionary containing the SMARTS representations of different
    functional groups loaded from the internal ``fgroup_smarts_comb.yml`` file.

    Returns
    -------
        A dictionary where each key is the name of a functional group and each value
        the corresponding SMARTS pattern.
    """

    file_name = resource_filename(
        "fragmenter", os.path.join("data", "fgroup_smarts_comb.yml")
    )

    with open(file_name, "r") as file:
        functional_groups = yaml.safe_load(file)

    return functional_groups
