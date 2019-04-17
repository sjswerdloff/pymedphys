# Copyright (C) 2019 Simon Biggs

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version (the "AGPL-3.0+").

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License and the additional terms for more
# details.

# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# ADDITIONAL TERMS are also included as allowed by Section 7 of the GNU
# Affero General Public License. These additional terms are Sections 1, 5,
# 6, 7, 8, and 9 from the Apache License, Version 2.0 (the "Apache-2.0")
# where all references to the definition "License" are instead defined to
# mean the AGPL-3.0+.

# You should have received a copy of the Apache-2.0 along with this
# program. If not, see <http://www.apache.org/licenses/LICENSE-2.0>.


from pydicom import Dataset

from ...libutils import get_imports
from ...xarray import XArrayComposition
from ...deliverydata import get_delivery_parameters

from .._level1.mudensitycore import calc_mu_density

IMPORTS = get_imports(globals())


class MUDensity(XArrayComposition):
    """Wrapper object for the calculation of MU Density given a range of
    formats
    """

    @classmethod
    def from_dicom(cls, ds: Dataset):
        """Calculate MU Density when provided with a pydicom dicom object"""
        return cls(None)


def mu_density_from_delivery_data(delivery_data):
    mu, mlc, jaw = get_delivery_parameters(delivery_data)
    xx, yy, mu_density = calc_mu_density(mu, mlc, jaw)

    return xx, yy, mu_density
