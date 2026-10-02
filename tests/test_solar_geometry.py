"""Independent geometry invariants and NOAA worked numerical checkpoints."""
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from tfm_photochem.m5_temporal import ReferenceEquinoxSolarCycle
from tfm_photochem.solar_geometry import (
    DatetimeSolarGeometry,
    solar_position,
    solar_zenith_angle,
)


def date(month,day,hour=12):
    return datetime(2020,month,day,hour,tzinfo=timezone.utc)


def test_noaa_numeric_checkpoints_and_equinox_reference():
    p=solar_position(date(3,20),45,0)
    assert p['equation_of_time_min']==pytest.approx(-7.9244120815,abs=1e-8)
    assert p['declination_deg']==pytest.approx(-.1511893470,abs=1e-8)
    assert p['sza_deg']==pytest.approx(45.1853357568,abs=1e-8)
    times=np.arange(0,86401,600.)
    clock=DatetimeSolarGeometry(date(3,20,0),45,0)
    assert np.max(abs(clock.sza(times)-ReferenceEquinoxSolarCycle().sza(times)))<1.6
    assert 44.8<clock.sza(43200)<45.4
    assert 134.5<clock.sza(0)<135.5


def test_utc_equivalence_and_longitude_east_positive():
    instant=date(3,20)
    assert solar_zenith_angle(instant,45,10)==solar_zenith_angle(
        instant.astimezone(timezone(timedelta(hours=-7))),45,10)
    # Positive 15 degrees advances solar time by one hour. Declination/EOT
    # evolve with UTC, so the shifted-instant comparison is approximate.
    assert solar_zenith_angle(date(3,20,10),45,15)==pytest.approx(
        solar_zenith_angle(date(3,20,11),45,0),abs=.03)
    assert solar_zenith_angle(date(3,20,10),45,15)<solar_zenith_angle(date(3,20,10),45,-15)
    assert solar_zenith_angle(instant,45,180)==solar_zenith_angle(instant,45,-180)


@pytest.mark.parametrize('month,day,north,south',[(6,21,21.55,68.46),(12,21,68.42,21.59)])
def test_solstices_and_hemisphere_reversal(month,day,north,south):
    assert solar_zenith_angle(date(month,day),45,0)==pytest.approx(north,abs=.08)
    assert solar_zenith_angle(date(month,day),-45,0)==pytest.approx(south,abs=.08)


def test_sunrise_sunset_and_polar_no_crossings():
    clock=DatetimeSolarGeometry(date(3,20,0),45,0)
    roots=clock.breakpoints(86400,[90.])
    assert len(roots)==4
    np.testing.assert_allclose(clock.sza(roots[1:-1]),90.,atol=1e-8)
    assert clock.sza(roots[1]-60)>90>clock.sza(roots[1]+60)
    assert clock.sza(roots[2]-60)<90<clock.sza(roots[2]+60)
    for latitude,month,day,illuminated in [(90,6,21,True),(90,12,21,False),
                                          (-90,6,21,False),(-90,12,21,True)]:
        polar=DatetimeSolarGeometry(date(month,day,0),latitude,0)
        assert np.all((polar.sza(np.linspace(0,86400,97))<90)==illuminated)
        np.testing.assert_array_equal(polar.breakpoints(86400,[90.]),[0.,86400.])


def test_short_grazing_twilight_extremum_is_not_missed():
    clock=DatetimeSolarGeometry(date(6,21,0),70,0)
    from scipy.optimize import minimize_scalar
    minimum=minimize_scalar(clock.sza,bounds=(40000,47000),method='bounded')
    zenith=minimum.fun+1e-5
    roots=clock.breakpoints(86400,[zenith])
    assert len(roots)==4
    assert roots[2]-roots[1]<900
    np.testing.assert_allclose(clock.sza(roots[1:-1]),zenith,atol=1e-8)


@pytest.mark.parametrize('lat,lon',[(91,0),(-91,0),(0,181),(0,-181),(np.nan,0),(0,np.inf)])
def test_invalid_locations(lat,lon):
    with pytest.raises(ValueError):
        solar_zenith_angle(date(3,20),lat,lon)


def test_naive_datetime_rejected_and_leap_midnight_continuity():
    with pytest.raises(ValueError):
        solar_zenith_angle(datetime(2020,3,20),45,0)
    clock=DatetimeSolarGeometry(datetime(2020,2,29,23,59,59,tzinfo=timezone.utc),45,0)
    assert abs(clock.sza(2)-clock.sza(0))<.01
