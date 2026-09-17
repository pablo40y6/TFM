"""Historical chemistry plus the M4C spherical-column UV calculation.

The three O2 excitation g-factors and the temporal solver remain external.
"""

from .background import frozen_asset_hashes, load_baseline_background
from .background_types import BackgroundCase, ChemicalBackground, RadiativeBackground
from .config import CONFIGURATION
from .fluxes import (
    BARTH_B0_ASSUMPTION,
    MODEL_ASSUMPTIONS,
    ODD_OXYGEN_PHOTOLYSIS_ASSUMPTION,
)
from .kinetics import RATE_LAWS, RateLaw
from .local_closure import close_local_chemistry
from .local_types import (
    AlgebraicState,
    LocalBackground,
    LocalClosureResult,
    LocalForcing,
    LocalState,
    LocalTendencies,
    ProductionLossDiagnostics,
    QSSAResiduals,
)
from .photolysis_budget import (
    GROSS_SUBSET_RELATIVE_TOLERANCE,
    PARTITION_RELATIVE_TOLERANCE,
    OddOxygenPhotolysisPartition,
    partition_odd_oxygen_photolysis,
)
from .qssa import (
    MultiplePhysicalRootsError,
    NoPhysicalRootError,
    QSSAError,
    SingularQSSAError,
)
from .reactions import REACTION_BY_ID, REACTIONS, SCALAR_PARAMETERS, Reaction
from .stoichiometry import SPECIAL_FLUX_RULES, TENDENCY_COEFFICIENTS
from .uv_assets import (
    CrossSectionTable,
    HistoricalUVAssets,
    UVSpectralBackbone,
    load_historical_uv_assets,
    uv_asset_hashes,
)
from .uv_cross_sections import (
    H2O2_LYMAN_ALPHA_SIGMA_CM2,
    h2o2_cross_section,
    h2o_channel_yields,
    h2o_cross_section,
)
from .uv_geometry import (
    CHEMISTRY_ALTITUDES_KM,
    EARTH_RADIUS_KM,
    SHELL_EDGES_KM,
    TOP_OF_COLUMN_KM,
    SphericalPathGeometry,
    spherical_shell_paths,
)
from .uv_radiation import (
    J_NAMES,
    SlantColumns,
    UVPhotolysisProfile,
    UVRadiationDiagnostics,
    attenuated_photon_flux,
    compute_uv_photolysis,
    local_forcing_from_uv,
    optical_depth,
    slant_columns,
)

__all__ = [
    "AlgebraicState",
    "BackgroundCase",
    "BARTH_B0_ASSUMPTION",
    "CONFIGURATION",
    "ChemicalBackground",
    "CHEMISTRY_ALTITUDES_KM",
    "CrossSectionTable",
    "EARTH_RADIUS_KM",
    "LocalBackground",
    "LocalClosureResult",
    "LocalForcing",
    "LocalState",
    "LocalTendencies",
    "MODEL_ASSUMPTIONS",
    "ODD_OXYGEN_PHOTOLYSIS_ASSUMPTION",
    "OddOxygenPhotolysisPartition",
    "GROSS_SUBSET_RELATIVE_TOLERANCE",
    "H2O2_LYMAN_ALPHA_SIGMA_CM2",
    "HistoricalUVAssets",
    "J_NAMES",
    "PARTITION_RELATIVE_TOLERANCE",
    "MultiplePhysicalRootsError",
    "NoPhysicalRootError",
    "ProductionLossDiagnostics",
    "QSSAError",
    "QSSAResiduals",
    "RadiativeBackground",
    "RATE_LAWS",
    "REACTIONS",
    "REACTION_BY_ID",
    "SCALAR_PARAMETERS",
    "SHELL_EDGES_KM",
    "SPECIAL_FLUX_RULES",
    "SingularQSSAError",
    "SlantColumns",
    "SphericalPathGeometry",
    "TENDENCY_COEFFICIENTS",
    "TOP_OF_COLUMN_KM",
    "UVPhotolysisProfile",
    "UVRadiationDiagnostics",
    "UVSpectralBackbone",
    "RateLaw",
    "Reaction",
    "close_local_chemistry",
    "compute_uv_photolysis",
    "attenuated_photon_flux",
    "frozen_asset_hashes",
    "load_baseline_background",
    "load_historical_uv_assets",
    "local_forcing_from_uv",
    "h2o2_cross_section",
    "h2o_channel_yields",
    "h2o_cross_section",
    "optical_depth",
    "partition_odd_oxygen_photolysis",
    "slant_columns",
    "spherical_shell_paths",
    "uv_asset_hashes",
]
