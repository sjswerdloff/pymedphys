# Copyright (C) 2018 Cancer Care Associates

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


import numpy as np


def find_relevant_control_points(mu):
    """Returns that control points that had an MU difference either side.
    """
    mu_diff = np.diff(mu)
    no_change = mu_diff == 0
    no_change_before = no_change[0:-1]
    no_change_after = no_change[1::]

    no_change_before_and_after = no_change_before & no_change_after
    irrelevant_control_point = np.hstack(
        [no_change[0], no_change_before_and_after, no_change[-1]])
    relevant_control_points = np.invert(irrelevant_control_point)

    return relevant_control_points


def remove_irrelevant_control_points(mu, mlc, jaw):
    """Removes control points that don't have MU delivery
    """
    assert len(mu) > 0, "No control points found"

    mu = np.array(mu)
    mlc = np.array(mlc)
    jaw = np.array(jaw)

    control_points_to_use = find_relevant_control_points(mu)

    mu = mu[control_points_to_use]
    mlc = mlc[control_points_to_use, :, :]
    jaw = jaw[control_points_to_use, :]

    return mu, mlc, jaw
