"""Versioned geometry for the source-locked R9/R18 Ricketts subset.

Only patient-observed geometry with explicitly versioned conventions is
implemented here. No norms, classification, diagnosis, prognosis or treatment
logic belongs in this module.
"""
from __future__ import annotations

import math
from typing import Optional, Tuple

Point = Tuple[float, float]
_EPS = 1e-12


def _cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _finite_points(*points: Point) -> bool:
    return all(math.isfinite(value) for point in points for value in point)


def _angle_deg(v1: Point, v2: Point) -> Optional[float]:
    len1 = math.hypot(*v1)
    len2 = math.hypot(*v2)
    if not all(math.isfinite(value) for value in (*v1, *v2, len1, len2)):
        return None
    if len1 <= _EPS or len2 <= _EPS:
        return None
    cosine = (v1[0] * v2[0] + v1[1] * v2[1]) / (len1 * len2)
    cosine = max(-1.0, min(1.0, cosine))
    angle = math.degrees(math.acos(cosine))
    return angle if math.isfinite(angle) else None


def ricketts_facial_depth_deg_v1(
    po: Point,
    or_: Point,
    n: Point,
    pog: Point,
) -> Optional[float]:
    """Posterior angle from anatomical Frankfort Po->Or to facial plane Pog->N."""
    if not _finite_points(po, or_, n, pog):
        return None
    return _angle_deg(
        (or_[0] - po[0], or_[1] - po[1]),
        (n[0] - pog[0], n[1] - pog[1]),
    )


def ricketts_constructed_gn_v1(
    n: Point,
    pog: Point,
    go: Point,
    me: Point,
) -> Optional[Point]:
    """Construct clinical Gn as intersection of N-Pog and Go-Me infinite lines."""
    if not _finite_points(n, pog, go, me):
        return None
    facial = (pog[0] - n[0], pog[1] - n[1])
    mandibular = (me[0] - go[0], me[1] - go[1])
    if math.hypot(*facial) <= _EPS or math.hypot(*mandibular) <= _EPS:
        return None
    denominator = _cross(facial, mandibular)
    if not math.isfinite(denominator) or abs(denominator) <= _EPS:
        return None
    delta = (go[0] - n[0], go[1] - n[1])
    t = _cross(delta, mandibular) / denominator
    gn = (n[0] + t * facial[0], n[1] + t * facial[1])
    return gn if _finite_points(gn) else None


def ricketts_facial_axis_deg_v1(
    ba: Point,
    n: Point,
    pt: Point,
    gn_constructed: Point,
) -> Optional[float]:
    """Inferior/non-reflex angle between Ba->N and Pt->constructed-Gn."""
    if not _finite_points(ba, n, pt, gn_constructed):
        return None
    return _angle_deg(
        (n[0] - ba[0], n[1] - ba[1]),
        (gn_constructed[0] - pt[0], gn_constructed[1] - pt[1]),
    )


def ricketts_convexity_signed_distance_px_v1(
    a: Point,
    n: Point,
    pog: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """Signed perpendicular A-to-NPog distance in source pixels."""
    if not _finite_points(a, n, pog, po, or_):
        return None
    facial = (pog[0] - n[0], pog[1] - n[1])
    facial_len_sq = facial[0] ** 2 + facial[1] ** 2
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    if facial_len_sq <= _EPS or fh_len <= _EPS:
        return None
    t = ((a[0] - n[0]) * facial[0] + (a[1] - n[1]) * facial[1]) / facial_len_sq
    projection = (n[0] + t * facial[0], n[1] + t * facial[1])
    residual = (a[0] - projection[0], a[1] - projection[1])
    magnitude = math.hypot(*residual)
    if not math.isfinite(magnitude):
        return None
    if magnitude <= _EPS:
        return 0.0
    anterior_score = residual[0] * (fh[0] / fh_len) + residual[1] * (fh[1] / fh_len)
    if not math.isfinite(anterior_score) or abs(anterior_score) <= _EPS:
        return None
    return math.copysign(magnitude, anterior_score)


def ricketts_e_line_horizontal_signed_distance_px_v1(
    lip: Point,
    prn: Point,
    pog_soft: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """Legacy V1: signed E-line displacement measured parallel to Frankfort.

    Retained only so persisted V1 evidence keeps immutable semantics. New R18
    evidence uses the source-strict perpendicular V2 convention below.
    """
    if not _finite_points(lip, prn, pog_soft, po, or_):
        return None
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    e_line = (pog_soft[0] - prn[0], pog_soft[1] - prn[1])
    if fh_len <= _EPS or math.hypot(*e_line) <= _EPS:
        return None
    anterior = (fh[0] / fh_len, fh[1] / fh_len)
    denominator = _cross(anterior, e_line)
    if not math.isfinite(denominator) or abs(denominator) <= _EPS:
        return None
    displacement = _cross((lip[0] - prn[0], lip[1] - prn[1]), e_line) / denominator
    return displacement if math.isfinite(displacement) else None


def ricketts_e_line_perpendicular_signed_distance_px_v2(
    lip: Point,
    prn: Point,
    pog_soft: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """R18 V2: signed shortest/perpendicular lip distance to Prn-Pog'.

    Magnitude is the perpendicular point-to-line distance. Frankfort Po->Or is
    used only to orient the sign (positive anterior, negative posterior), never
    to change the distance magnitude. V2 is mirror-invariant and matches the
    source-strict cephalometric E-line definition used by the runtime/frontend.
    """
    if not _finite_points(lip, prn, pog_soft, po, or_):
        return None
    e_line = (pog_soft[0] - prn[0], pog_soft[1] - prn[1])
    e_len_sq = e_line[0] ** 2 + e_line[1] ** 2
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    if e_len_sq <= _EPS or fh_len <= _EPS:
        return None
    t = ((lip[0] - prn[0]) * e_line[0] + (lip[1] - prn[1]) * e_line[1]) / e_len_sq
    projection = (prn[0] + t * e_line[0], prn[1] + t * e_line[1])
    residual = (lip[0] - projection[0], lip[1] - projection[1])
    magnitude = math.hypot(*residual)
    if not math.isfinite(magnitude):
        return None
    if magnitude <= _EPS:
        return 0.0
    anterior_score = residual[0] * (fh[0] / fh_len) + residual[1] * (fh[1] / fh_len)
    if not math.isfinite(anterior_score) or abs(anterior_score) <= _EPS:
        return None
    return math.copysign(magnitude, anterior_score)


def ricketts_mandibular_plane_fh_deg_v1(
    po: Point,
    or_: Point,
    go_ricketts: Point,
    me: Point,
) -> Optional[float]:
    """Angle between anatomical Frankfort and the source-specific Ricketts mandibular plane.

    The mandibular plane is defined by the inferior border of the mandibular
    angle and Menton. Generic Go identities are not promoted silently.
    """
    if not _finite_points(po, or_, go_ricketts, me):
        return None
    return _angle_deg(
        (or_[0] - po[0], or_[1] - po[1]),
        (me[0] - go_ricketts[0], me[1] - go_ricketts[1]),
    )


def ricketts_maxillary_depth_deg_v1(
    po: Point,
    or_: Point,
    n: Point,
    a: Point,
) -> Optional[float]:
    """Angle between anatomical Frankfort Po->Or and N->A.

    This is the source-specific Ricketts maxillary-depth geometry. No norm,
    classification or age adjustment is applied here.
    """
    if not _finite_points(po, or_, n, a):
        return None
    return _angle_deg(
        (or_[0] - po[0], or_[1] - po[1]),
        (a[0] - n[0], a[1] - n[1]),
    )


def ricketts_l1_apog_inclination_deg_v1(
    l1_incisal: Point,
    l1_apex: Point,
    a: Point,
    pog: Point,
) -> Optional[float]:
    """Angle between lower-incisor long axis and the Ricketts A-Pog line.

    The lower-incisor axis is oriented incisal->apex so the clinical angle is
    the small angle used by the Ricketts A-Pog inclination convention.
    """
    if not _finite_points(l1_incisal, l1_apex, a, pog):
        return None
    return _angle_deg(
        (l1_apex[0] - l1_incisal[0], l1_apex[1] - l1_incisal[1]),
        (pog[0] - a[0], pog[1] - a[1]),
    )


def ricketts_l1_edge_apog_signed_distance_px_v1(
    l1_incisal: Point,
    a: Point,
    pog: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """Signed perpendicular distance from lower incisal edge to A-Pog.

    Magnitude is the shortest point-to-line distance. Frankfort Po->Or is used
    only to orient the sign: positive anterior to A-Pog, negative posterior.
    No norm or classification is applied here.
    """
    if not _finite_points(l1_incisal, a, pog, po, or_):
        return None
    apog = (pog[0] - a[0], pog[1] - a[1])
    apog_len_sq = apog[0] ** 2 + apog[1] ** 2
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    if apog_len_sq <= _EPS or fh_len <= _EPS:
        return None
    t = ((l1_incisal[0] - a[0]) * apog[0] + (l1_incisal[1] - a[1]) * apog[1]) / apog_len_sq
    projection = (a[0] + t * apog[0], a[1] + t * apog[1])
    residual = (l1_incisal[0] - projection[0], l1_incisal[1] - projection[1])
    magnitude = math.hypot(*residual)
    if not math.isfinite(magnitude):
        return None
    if magnitude <= _EPS:
        return 0.0
    anterior_score = residual[0] * (fh[0] / fh_len) + residual[1] * (fh[1] / fh_len)
    if not math.isfinite(anterior_score) or abs(anterior_score) <= _EPS:
        return None
    return math.copysign(magnitude, anterior_score)


def ricketts_u1_edge_apog_signed_distance_px_v1(
    u1_incisal: Point,
    a: Point,
    pog: Point,
    po: Point,
    or_: Point,
) -> Optional[float]:
    """Signed perpendicular distance from upper incisal edge to A-Pog.

    Atlas/Ricketts source lock matches the lower-incisor construction:
    shortest point-to-line distance with positive sign anterior to A-Pog.
    Frankfort Po->Or orients anterior/posterior only.
    """
    return ricketts_l1_edge_apog_signed_distance_px_v1(
        u1_incisal, a, pog, po, or_
    )


def ricketts_l1_occlusal_extrusion_signed_px_v1(
    l1_incisal: Point,
    l1_apex: Point,
    plane_point: Point,
    plane_direction: Point,
) -> Optional[float]:
    """Signed perpendicular lower-incisor distance to the Ricketts functional occlusal plane.

    Positive is the crownward/incisal side of the plane (greater extrusion /
    supraocclusion); negative is the apical side (reduced extrusion / open-bite
    direction). The lower-incisor long axis orients the plane normal, making the
    sign independent of image rotation or horizontal mirroring.
    """
    if not _finite_points(l1_incisal, l1_apex, plane_point, plane_direction):
        return None
    plane_len = math.hypot(*plane_direction)
    incisal_axis = (
        l1_incisal[0] - l1_apex[0],
        l1_incisal[1] - l1_apex[1],
    )
    axis_len = math.hypot(*incisal_axis)
    if plane_len <= _EPS or axis_len <= _EPS:
        return None

    normal = (-plane_direction[1] / plane_len, plane_direction[0] / plane_len)
    orientation = normal[0] * incisal_axis[0] + normal[1] * incisal_axis[1]
    if not math.isfinite(orientation) or abs(orientation) <= _EPS:
        return None
    if orientation < 0:
        normal = (-normal[0], -normal[1])

    signed_distance = (
        (l1_incisal[0] - plane_point[0]) * normal[0]
        + (l1_incisal[1] - plane_point[1]) * normal[1]
    )
    return signed_distance if math.isfinite(signed_distance) else None


def ricketts_xi_from_r1_r4_fh_v1(
    r1: Point,
    r2: Point,
    r3: Point,
    r4: Point,
    po: Point,
    or_: Point,
) -> Optional[Point]:
    """Construct Xi as the center of the Ricketts ramal rectangle.

    R1/R2 define the opposed ramal limits along the Frankfort axis; R3/R4
    define the superior/inferior limits along the perpendicular axis. The
    construction is expressed in the anatomical Frankfort basis so it is
    invariant to image rotation and mirroring.
    """
    if not _finite_points(r1, r2, r3, r4, po, or_):
        return None
    fh = (or_[0] - po[0], or_[1] - po[1])
    fh_len = math.hypot(*fh)
    if fh_len <= _EPS:
        return None
    u = (fh[0] / fh_len, fh[1] / fh_len)
    v = (-u[1], u[0])

    h1 = r1[0] * u[0] + r1[1] * u[1]
    h2 = r2[0] * u[0] + r2[1] * u[1]
    k3 = r3[0] * v[0] + r3[1] * v[1]
    k4 = r4[0] * v[0] + r4[1] * v[1]
    if abs(h1 - h2) <= _EPS or abs(k3 - k4) <= _EPS:
        return None

    h = (h1 + h2) / 2.0
    k = (k3 + k4) / 2.0
    xi = (h * u[0] + k * v[0], h * u[1] + k * v[1])
    return xi if _finite_points(xi) else None


def ricketts_lower_facial_height_ans_xi_pm_deg_v1(
    ans: Point,
    xi: Point,
    pm: Point,
) -> Optional[float]:
    """Oral-gnomon/lower-facial-height angle ANS-Xi-Pm with vertex at Xi."""
    if not _finite_points(ans, xi, pm):
        return None
    return _angle_deg(
        (ans[0] - xi[0], ans[1] - xi[1]),
        (pm[0] - xi[0], pm[1] - xi[1]),
    )


def ricketts_mandibular_arc_deg_v1(
    dc: Point,
    xi: Point,
    pm: Point,
) -> Optional[float]:
    """Ricketts mandibular arc / bend angle at Xi.

    The condylar axis is Xi→DC. The comparison axis is the posterior extension
    of the corpus axis Xi→Pm, therefore its direction at Xi is Pm→Xi.
    """
    if not _finite_points(dc, xi, pm):
        return None
    return _angle_deg(
        (dc[0] - xi[0], dc[1] - xi[1]),
        (xi[0] - pm[0], xi[1] - pm[1]),
    )


def ricketts_u6_distal_to_ptv_signed_px_v1(
    u6_distal: Point,
    pr_ptv: Point,
    anterior_direction: Point,
) -> Optional[float]:
    """Signed U6 A6-to-PTV distance using the canonical PTV anterior axis."""
    if not _finite_points(u6_distal, pr_ptv, anterior_direction):
        return None
    axis_len = math.hypot(*anterior_direction)
    if axis_len <= _EPS:
        return None
    anterior = (
        anterior_direction[0] / axis_len,
        anterior_direction[1] / axis_len,
    )
    delta = (u6_distal[0] - pr_ptv[0], u6_distal[1] - pr_ptv[1])
    value = delta[0] * anterior[0] + delta[1] * anterior[1]
    return value if math.isfinite(value) else None


def ricketts_signed_projection_on_plane_px_v1(
    first: Point,
    second: Point,
    plane_direction: Point,
) -> Optional[float]:
    """Signed first-minus-second separation along a source-locked plane."""
    if not _finite_points(first, second, plane_direction):
        return None
    norm = math.hypot(*plane_direction)
    if norm <= _EPS:
        return None
    unit = (plane_direction[0] / norm, plane_direction[1] / norm)
    delta = (first[0] - second[0], first[1] - second[1])
    value = delta[0] * unit[0] + delta[1] * unit[1]
    return value if math.isfinite(value) else None


def ricketts_u1_apog_inclination_deg_v1(
    u1_incisal: Point,
    u1_apex: Point,
    a: Point,
    pog: Point,
) -> Optional[float]:
    """Acute line angle between the maxillary-incisor long axis and A-Pog."""
    if not _finite_points(u1_incisal, u1_apex, a, pog):
        return None
    angle = _angle_deg(
        (u1_apex[0] - u1_incisal[0], u1_apex[1] - u1_incisal[1]),
        (pog[0] - a[0], pog[1] - a[1]),
    )
    if angle is None:
        return None
    return min(angle, 180.0 - angle)


def ricketts_line_angle_acute_deg_v1(
    first_direction: Point,
    second_direction: Point,
) -> Optional[float]:
    """Acute/non-oriented angle between two source-locked cephalometric lines."""
    if not _finite_points(first_direction, second_direction):
        return None
    angle = _angle_deg(first_direction, second_direction)
    if angle is None:
        return None
    return min(angle, 180.0 - angle)


def ricketts_upper_lip_length_px_v1(
    ans: Point,
    labial_commissure: Point,
) -> Optional[float]:
    """Atlas/Ricketts upper-lip length: straight-line ANS to labial commissure."""
    if not _finite_points(ans, labial_commissure):
        return None
    value = math.hypot(
        labial_commissure[0] - ans[0],
        labial_commissure[1] - ans[1],
    )
    return value if math.isfinite(value) else None


def ricketts_maxillary_height_n_cf_a_deg_v1(
    n: Point,
    cf: Point,
    a: Point,
) -> Optional[float]:
    """Ricketts maxillary height: N-CF-A angle with vertex at CF."""
    if not _finite_points(n, cf, a):
        return None
    return _angle_deg(
        (n[0] - cf[0], n[1] - cf[1]),
        (a[0] - cf[0], a[1] - cf[1]),
    )



def ricketts_point_distance_px_v1(first: Point, second: Point) -> Optional[float]:
    """Euclidean source-image distance between two source-locked landmarks."""
    if not _finite_points(first, second):
        return None
    value = math.hypot(second[0] - first[0], second[1] - first[1])
    return value if math.isfinite(value) else None


def ricketts_cc_atlas2009_v1(
    ba: Point,
    n: Point,
    pt: Point,
    gn: Point,
) -> Optional[Point]:
    """Atlas-2009 CC: intersection of Ba-N and the facial axis Pt-Gn."""
    if not _finite_points(ba, n, pt, gn):
        return None
    ban = (n[0] - ba[0], n[1] - ba[1])
    facial_axis = (gn[0] - pt[0], gn[1] - pt[1])
    if math.hypot(*ban) <= _EPS or math.hypot(*facial_axis) <= _EPS:
        return None
    denominator = _cross(ban, facial_axis)
    if not math.isfinite(denominator) or abs(denominator) <= _EPS:
        return None
    delta = (pt[0] - ba[0], pt[1] - ba[1])
    t = _cross(delta, facial_axis) / denominator
    point = (ba[0] + t * ban[0], ba[1] + t * ban[1])
    return point if _finite_points(point) else None


def ricketts_cranial_deflection_deg_v1(
    po: Point,
    or_: Point,
    ba: Point,
    n: Point,
) -> Optional[float]:
    """Ricketts cranial deflection: acute angle anatomical FH / Ba-N."""
    if not _finite_points(po, or_, ba, n):
        return None
    return ricketts_line_angle_acute_deg_v1(
        (or_[0] - po[0], or_[1] - po[1]),
        (n[0] - ba[0], n[1] - ba[1]),
    )


def ricketts_total_facial_height_deg_v1(
    ba: Point,
    n: Point,
    xi: Point,
    pm: Point,
) -> Optional[float]:
    """Ricketts total facial height: acute angle Ba-N / Pm-Xi."""
    if not _finite_points(ba, n, xi, pm):
        return None
    return ricketts_line_angle_acute_deg_v1(
        (n[0] - ba[0], n[1] - ba[1]),
        (xi[0] - pm[0], xi[1] - pm[1]),
    )


def ricketts_ramus_position_deg_v1(
    po: Point,
    or_: Point,
    cf: Point,
    xi: Point,
) -> Optional[float]:
    """Ricketts ramus position: acute angle anatomical FH / CF-Xi."""
    if not _finite_points(po, or_, cf, xi):
        return None
    return ricketts_line_angle_acute_deg_v1(
        (or_[0] - po[0], or_[1] - po[1]),
        (xi[0] - cf[0], xi[1] - cf[1]),
    )


def ricketts_porion_location_signed_px_v1(
    po: Point,
    ptv_point: Point,
    anterior_direction: Point,
) -> Optional[float]:
    """Signed PTV-to-Porion distance along Frankfort; posterior is negative."""
    return ricketts_signed_projection_on_plane_px_v1(
        po, ptv_point, anterior_direction
    )
