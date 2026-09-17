"""Parameters appearing in the literal 2017 MATLAB routines."""

from types import MappingProxyType

from tfm_photochem.metadata import Parameter

_REF = "Li (2017), MSc thesis, Appendix A.4/A.10/A.11 MATLAB listing"
_CFG = "legacy_2017"

PARAMETERS = MappingProxyType(
    {
        "earth_radius": Parameter(6370.0, "km", _REF, 2017, _CFG),
        "o_o2_m_preexponential": Parameter(
            6.0e-34, "cm6 molecule-2 s-1", _REF, 2017, _CFG
        ),
        "o_o2_m_temperature_scale": Parameter(300.0, "K", _REF, 2017, _CFG),
        "o_o2_m_exponential_power": Parameter(
            2.3,
            "1",
            _REF,
            2017,
            _CFG,
            "Literal exp(300/T)^2.3 expression, not the historical_2020 law.",
        ),
        "o_o3_preexponential": Parameter(
            8.0e-12, "cm3 molecule-1 s-1", _REF, 2017, _CFG
        ),
        "o_o3_activation_temperature": Parameter(2060.0, "K", _REF, 2017, _CFG),
        "hartley_lower_exclusive": Parameter(210.0, "nm", _REF, 2017, _CFG),
        "hartley_upper_exclusive": Parameter(310.0, "nm", _REF, 2017, _CFG),
        "src_lower_exclusive": Parameter(122.0, "nm", _REF, 2017, _CFG),
        "src_upper_exclusive": Parameter(175.0, "nm", _REF, 2017, _CFG),
        "lya_matlab_index": Parameter(
            28,
            "1-based index",
            _REF,
            2017,
            _CFG,
            "Corresponds to 121.567 nm in the frozen asset.",
        ),
        "km_to_cm": Parameter(1.0e5, "cm km-1", _REF, 2017, _CFG),
        "mkozone_fixed_point_passes": Parameter(3, "count", _REF, 2017, _CFG),
    }
)


def value(name: str) -> float | int:
    """Return a parameter's numerical value."""

    return PARAMETERS[name].value

