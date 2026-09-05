import unittest

from github_repo_health.github_api import MAX_LIMIT, repository_path, validate_limit


class GitHubApiTests(unittest.TestCase):
    def test_repository_path_strips_whitespace(self):
        self.assertEqual(repository_path(" octocat ", " hello-world "), "/repos/octocat/hello-world")

    def test_repository_path_requires_owner_and_repo(self):
        with self.assertRaises(ValueError):
            repository_path("", "hello-world")

    def test_validate_limit_accepts_supported_range(self):
        self.assertEqual(validate_limit(10), 10)
        self.assertEqual(validate_limit(MAX_LIMIT), MAX_LIMIT)

    def test_validate_limit_rejects_out_of_range_values(self):
        with self.assertRaises(ValueError):
            validate_limit(0)
        with self.assertRaises(ValueError):
            validate_limit(MAX_LIMIT + 1)


if __name__ == "__main__":
    unittest.main()