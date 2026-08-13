import unittest

from core.release import channel_allows_version


class ReleasePolicyTests(unittest.TestCase):
    def test_stable_accepts_only_final_semantic_versions(self):
        self.assertTrue(channel_allows_version("stable", "v1.0.0"))
        self.assertFalse(channel_allows_version("stable", "v1.0.0-beta.1"))
        self.assertFalse(channel_allows_version("stable", "develop"))

    def test_beta_accepts_final_and_prerelease_semantic_versions(self):
        self.assertTrue(channel_allows_version("beta", "v1.0.0"))
        self.assertTrue(channel_allows_version("beta", "v1.1.0-beta.2"))
        self.assertFalse(channel_allows_version("beta", "feature/foo"))


if __name__ == "__main__":
    unittest.main()
