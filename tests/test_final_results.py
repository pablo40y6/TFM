"""Independent checks on reporting conventions, not new model acceptance gates."""
import numpy as np
import pytest

from scripts.plot_final_results import at_sza, sensitivity
from scripts.run_final_results import scenario


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
