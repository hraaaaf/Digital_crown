"""Synthetic ONLY registration tests; screenshot is never published in CI."""
from __future__ import annotations

import copy
import math
import unittest

from audit import cephalo_facad_p5_overlay_registration as p5


class FakeRGB:
    mode = "RGB"
    size = (520, 520)

    def __init__(self):
        self.pixels = {}

    def getpixel(self, pos):
        return self.pixels.get(tuple(pos), (20, 20, 20))

    def dot(self, x, y, rgb=(255, 0, 0)):
        x,y = round(x),round(y)
        for dy in range(-1,2):
            for dx in range(-1,2):
                self.pixels[x+dx,y+dy] = rgb


def synthetic():
    points = {"S": (12.0,18.0), "N": (30.0,24.0)}
    points.update({f"fake{i}": (10.0+(i%7)*12.0, 35.0+(i//7)*12.0)
                   for i in range(28)})
    anchors = {name: (4*x+40,4*y+60) for name,(x,y) in points.items()
               if name in {"S","N"}}
    image = FakeRGB()
    for name,(x,y) in points.items():
        if name != "fake17":
            image.dot(4*x+40,4*y+60)
    return image, points, anchors


class OverlayEvidenceIsNotClinicalIdentity(unittest.TestCase):
    def test_two_anchor_similarity_recovers_known_registration(self):
        image, points, anchors = synthetic()
        coeff, offset = p5.similarity_from_two_anchors(points, anchors)
        self.assertAlmostEqual(coeff.real, 4.0)
        self.assertAlmostEqual(coeff.imag, 0.0)
        self.assertAlmostEqual(offset.real, 40.0)
        self.assertAlmostEqual(offset.imag, 60.0)

    def test_out_of_sample_red_hit_sanity_not_landmark_authority(self):
        image, points, anchors = synthetic()
        result = p5.assess(image, points, anchors)
        self.assertEqual(result["fitted_anchor_count"], 2)
        self.assertEqual(result["out_of_sample_point_count"], 28)
        self.assertEqual(result["red_overlay_hits_total"], 29)
        self.assertEqual(result["red_overlay_hits_out_of_sample"], 27)
        self.assertEqual(result["red_overlay_misses"], ["fake17"])
        self.assertFalse(result["marker_anatomical_placement_independently_verified"])
        self.assertFalse(result["dc_pog_hard_identity_authorized"])
        self.assertEqual(result["clinical_parity_count"], 0)
        self.assertTrue(result["clinical_no_go"])

    def test_exported_red_point_cannot_become_clinically_valid_automatically(self):
        image,points,anchors=synthetic()
        image.dot(*[4*c+off for c,off in zip(points["fake17"],(40,60))])
        result=p5.assess(image,points,anchors)
        self.assertEqual(result["red_overlay_hits_total"],30)
        self.assertFalse(result["source_display_coordinate_frame_clinically_verified"])
        self.assertFalse(result["marker_anatomical_placement_independently_verified"])
        self.assertEqual(result["clinical_parity_count"],0)

    def test_rgb_grayscale_pixel_is_not_a_red_marker(self):
        image,points,anchors=synthetic()
        image.pixels.clear()
        for name,(x,y) in points.items():
            image.dot(4*x+40,4*y+60,(255,255,255))
        result=p5.assess(image,points,anchors)
        self.assertEqual(result["red_overlay_hits_total"],0)

    def test_refuse_missing_or_extra_anchors(self):
        _,points,anchors=synthetic()
        with self.assertRaisesRegex(ValueError,"exactly two"):
            p5.similarity_from_two_anchors(points, {"S": anchors["S"]})
        with self.assertRaisesRegex(ValueError,"exactly two"):
            p5.similarity_from_two_anchors(points, {**anchors,"fake0":(1,1)})

    def test_refuse_anchor_without_export(self):
        _,points,anchors=synthetic()
        with self.assertRaisesRegex(ValueError,"anchor missing"):
            p5.similarity_from_two_anchors(points, {"S":anchors["S"],"New":(20,20)})

    def test_refuse_identical_anchor_and_nonfinite_coordinates(self):
        _,points,anchors=synthetic()
        invalid=copy.deepcopy(points)
        invalid["N"]=invalid["S"]
        with self.assertRaisesRegex(ValueError,"ill-conditioned"):
            p5.similarity_from_two_anchors(invalid,anchors)
        bad=copy.deepcopy(anchors)
        bad["N"]=(math.nan,1.0)
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            p5.similarity_from_two_anchors(points,bad)

    def test_refuse_oversized_radius_or_unbounded_scan(self):
        image,points,anchors=synthetic()
        with self.assertRaisesRegex(ValueError,"overlay criteria"):
            p5.assess(image,points,anchors,radius_px=100)

    def test_non_rgb_image_rejected(self):
        image,points,anchors=synthetic()
        image.mode="L"
        with self.assertRaisesRegex(ValueError,"RGB"):
            p5.assess(image,points,anchors)


if __name__ == "__main__":
    unittest.main()
