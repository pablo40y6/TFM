"""NOAA fractional-year geometric solar position, with explicit UTC semantics.

Equations: https://gml.noaa.gov/grad/solcalc/solareqns.PDF (pp. 1-2).
This is the documented Fourier approximation, not a precision ephemeris.
No refraction or solar-disk correction is applied to the geometric zenith.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
from scipy.optimize import brentq


def utc_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(timezone.utc)


def validate_location(latitude, longitude):
    if not np.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("latitude must be finite and in [-90,90]")
    if not np.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("east-positive longitude must be finite and in [-180,180]")


def solar_position(when: datetime, latitude: float, longitude: float) -> dict:
    """Geometric SZA [deg], declination [deg], equation of time [minutes]."""
    when = utc_datetime(when)
    validate_location(latitude, longitude)
    hour = when.hour + when.minute/60 + (when.second + when.microsecond/1e6)/3600
    gamma = 2*np.pi/(366 if calendar.isleap(when.year) else 365)*(
        when.timetuple().tm_yday - 1 + (hour-12)/24)
    equation = 229.18*(.000075 + .001868*np.cos(gamma) - .032077*np.sin(gamma)
                       - .014615*np.cos(2*gamma) - .040849*np.sin(2*gamma))
    declination = (.006918 - .399912*np.cos(gamma) + .070257*np.sin(gamma)
                   - .006758*np.cos(2*gamma) + .000907*np.sin(2*gamma)
                   - .002697*np.cos(3*gamma) + .00148*np.sin(3*gamma))
    hour_angle = np.deg2rad((hour*60 + equation + 4*longitude)/4 - 180)
    lat = np.deg2rad(latitude)
    cosine = np.sin(lat)*np.sin(declination) + np.cos(lat)*np.cos(declination)*np.cos(hour_angle)
    # Roundoff guard on a geometric cosine; never concentration projection.
    zenith = np.rad2deg(np.arccos(np.clip(cosine, -1., 1.)))
    return dict(sza_deg=float(zenith), declination_deg=float(np.rad2deg(declination)),
                equation_of_time_min=float(equation))


def solar_zenith_angle(when: datetime, latitude: float, longitude: float) -> float:
    return solar_position(when, latitude, longitude)["sza_deg"]


@dataclass(frozen=True)
class DatetimeSolarGeometry:
    """Elapsed seconds from an explicit UTC origin, including polar day/night."""
    start_datetime: datetime
    latitude: float
    longitude: float

    def __post_init__(self):
        object.__setattr__(self, "start_datetime", utc_datetime(self.start_datetime))
        validate_location(self.latitude, self.longitude)

    def sza(self, time_s):
        times = np.asarray(time_s, dtype=float)
        if not np.all(np.isfinite(times)):
            raise ValueError("elapsed seconds must be finite")
        def angle(t):
            return solar_zenith_angle(self.start_datetime + timedelta(seconds=float(t)),
                                      self.latitude, self.longitude)
        result = np.array([angle(t) for t in times.ravel()]).reshape(times.shape)
        return float(result) if times.ndim == 0 else result

    def breakpoints(self, duration_s, zeniths):
        """Bracket crossings on monotone intervals, also locating polar extrema.

        Extrema are found from the derivative independently of the requested
        zeniths, so two crossings around a short grazing twilight are retained.
        Exact tangencies are integration boundaries too, without asserting a
        ground sunrise at 90.833 degrees or overriding shell shadow.
        """
        if not np.isfinite(duration_s) or duration_s <= 0:
            raise ValueError("positive finite duration required")
        grid = np.linspace(0., duration_s, max(3, int(np.ceil(duration_s/900))+1))
        def derivative(t):
            return (self.sza(t+1.)-self.sza(t-1.))/2
        slopes = [derivative(t) for t in grid]
        extrema = []
        for a,b,da,db in zip(grid[:-1],grid[1:],slopes[:-1],slopes[1:],strict=True):
            if da*db < 0:
                extrema.append(brentq(derivative,a,b,xtol=1e-6))
        anchors = np.unique(np.r_[grid,extrema])
        angles = self.sza(anchors)
        crossings = [0.,duration_s]
        for zenith in zeniths:
            delta = angles - zenith
            for a,b,da,db in zip(anchors[:-1],anchors[1:],delta[:-1],delta[1:],strict=True):
                if abs(da) < 1e-10:
                    crossings.append(a)
                if da*db < 0:
                    crossings.append(brentq(lambda t:self.sza(t)-zenith,a,b,xtol=1e-7))
        return np.unique(crossings)

    def metadata(self):
        return dict(algorithm="NOAA fractional-year Fourier approximation",
                    source="https://gml.noaa.gov/grad/solcalc/solareqns.PDF",
                    origin_utc=self.start_datetime.isoformat(), latitude_deg=self.latitude,
                    longitude_deg_east=self.longitude, zenith_units="degrees",
                    refraction=False, shadow="accepted spherical solid-Earth shell geometry")
