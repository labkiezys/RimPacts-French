import unittest

from tools.build_release import ROOT, manifest


class ReleasePreviewTests(unittest.TestCase):
    def test_manifest_includes_workshop_preview(self) -> None:
        self.assertIn(ROOT / "About" / "Preview.png", manifest())


if __name__ == "__main__":
    unittest.main()
