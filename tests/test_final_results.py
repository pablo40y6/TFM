"""Independent checks on reporting conventions, not new model acceptance gates."""
import numpy as np
import pytest

from scripts.plot_final_results import at_sza, sensitivity
from scripts.run_final_results import scenario
from tfm_photochem.dynamic_atmosphere import (
    DynamicMSISAtmosphere,
    _time_within_coverage,
)
from tfm_photochem.dynamic_radiation import DynamicNIRForcing
from tfm_photochem.m5_temporal import NIRForcingTable


def test_saved_output_interpolation_is_positive_and_has_no_extrapolation():
    angle = np.array([99., 90., 70.])
    values = np.array([[0., 9.], [18., 0.], [38., 20.]])
    np.testing.assert_array_equal(at_sza(angle, values, 80.), [28., 10.])
    assert at_sza(angle, values, 60.) is None
    assert at_sza(angle, values, 100.) is None
    assert np.all(at_sza(angle, values, 95.) >= 0)


def test_phase_selection_rejects_nonmonotonic_and_duplicate_sza():
    for angle in ([99., 70., 90.], [99., 90., 90.]):
        with pytest.raises(ValueError, match="decrease strictly"):
            at_sza(np.array(angle), np.ones((3, 2)), 90.)


def test_percentages_do_not_amplify_zero_concentrations():
    a = np.array([[0., 10.], [0.1, 20.]])
    b = np.array([[0.2, 20.], [0.3, 10.]])
    stats, relative, relevant = sensitivity(a, b, np.array([99., 85.]), np.array([0., 1.]), 1.)
    assert stats["max_percent"] == 50.
    assert stats["near_zero_absolute_max_cm3"] == pytest.approx(.2)
    np.testing.assert_array_equal(relevant[:, 0], False)
    np.testing.assert_array_equal(relative[:, 0], 0.)
    swapped, _, _ = sensitivity(b, a, np.array([99., 85.]), np.array([0., 1.]), 1.)
    assert swapped == stats


def test_campaign_does_not_claim_unreachable_zenith_angles():
    winter = scenario("winter")
    high = scenario("high_latitude")
    assert not winter["reaches_sza60"] and not high["reaches_sza60"]
    assert 68. < winter["attainable_minimum_sza_deg"] < 69.
    assert 69. < high["attainable_minimum_sza_deg"] < 70.
    assert scenario("reference")["reaches_sza60"]


def test_datetime_sum_endpoint_roundoff_and_real_outside_rejection():
    from datetime import datetime
    from types import SimpleNamespace

    config = scenario("equatorial")
    start, end, begin = (datetime.fromisoformat(config[k]) for k in
                        ("start_datetime_utc", "end_datetime_utc", "previous_noon_utc"))
    endpoint = (end-begin).total_seconds()
    query = (start-begin).total_seconds()+(end-start).total_seconds()
    assert query-endpoint == np.spacing(endpoint)  # Actual campaign witness.
    assert _time_within_coverage(query,0.,endpoint)==endpoint
    assert _time_within_coverage(endpoint/3,0.,endpoint)==endpoint/3
    provider = DynamicMSISAtmosphere.__new__(DynamicMSISAtmosphere)
    provider.times = np.array([0.,endpoint])
    provider.raw = np.arange(2*151*11,dtype=float).reshape(2,151,11)
    np.testing.assert_array_equal(provider.raw_at(query),provider.raw[-1])
    nir = DynamicNIRForcing.__new__(DynamicNIRForcing)
    nir.atmosphere = SimpleNamespace(times=provider.times)
    values = np.ones((2,51,3))
    values[1] = 0.  # The synthetic angular table must also preserve exact shadow.
    nir.tables = [NIRForcingTable([0.,180.],values) for _ in range(2)]
    np.testing.assert_array_equal(nir(query,60.),nir(endpoint,60.))
    for outside in (-1e-6,endpoint+1e-6):
        with pytest.raises(ValueError,match="coverage"):
            provider.raw_at(outside)
        with pytest.raises(ValueError,match="coverage"):
            nir(outside,60.)
