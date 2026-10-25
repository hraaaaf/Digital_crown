"""Fail-closed regression tests for the cross-app theme token scanner."""
from __future__ import annotations

import unittest

from scripts.ci import theme_token_policy as policy


class ThemeTokenPolicyTests(unittest.TestCase):
    def test_fixed_palette_in_every_state_is_rejected(self):
        for css_class in (
            "bg-white", "text-black", "bg-slate-900", "text-indigo-700",
            "border-red-500", "hover:bg-amber-400/20",
            "dark:hover:text-emerald-500", "focus-visible:ring-blue-300",
        ):
            with self.subTest(value=css_class):
                self.assertTrue(policy.signatures('className="' + css_class + '"'),
                                css_class)

    def test_arbitrary_palette_cannot_bypass_policy(self):
        for css_class in ("bg-[#1c1c21]", "text-[#fff]", "border-[rgba(255,0,0,0.5)]"):
            with self.subTest(value=css_class):
                self.assertIn("arbitrary:" + css_class,
                              policy.signatures('className="' + css_class + '"'))

    def test_literal_inline_css_colors_are_rejected(self):
        self.assertTrue(policy.signatures("color: '#fb7185'"))
        self.assertTrue(policy.signatures("background-color: #000"))
        self.assertTrue(policy.signatures("backgroundColor: 'rgba(212,175,55,.8)'"))

    def test_semantic_theme_roles_are_accepted(self):
        semantic = (
            'className="bg-background text-text-main border-border-main '
            'hover:bg-input-field bg-primary text-on-primary '
            'bg-warning-surface text-warning bg-info-surface '
            'bg-danger-surface text-danger"'
        )
        self.assertEqual(policy.signatures(semantic), {})

    def test_tests_and_theme_definitions_are_excluded(self):
        self.assertFalse(policy.production_source("frontend/src/index.css"))
        self.assertFalse(policy.production_source("frontend/src/examples/example.test.tsx"))
        self.assertFalse(policy.production_source("frontend/src/components/FakeLab.tsx"))
        self.assertTrue(policy.production_source("frontend/src/components/ErrorBoundary.tsx"))


if __name__ == "__main__":
    unittest.main()
