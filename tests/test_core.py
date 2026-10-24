from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile
import unittest
from zipfile import ZipFile

from skillproof.cli import main
from skillproof.core import catalog, diagram, discover, failed, inspect, pack, report


class SkillProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def skill(self, name="demo", front=None, body="# Work\n\nWrite a verified deliverable.", parent=None):
        directory = (parent or self.root) / name
        directory.mkdir(parents=True)
        front = front if front is not None else f"name: {name}\ndescription: Write project documentation when onboarding users."
        (directory / "SKILL.md").write_text(f"---\n{front}\n---\n\n{body}\n", encoding="utf-8")
        return directory

    def rules(self, path):
        return {f.rule for s in inspect(path) for f in s.findings}

    def cli(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main([str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def test_valid_skill(self):
        self.assertFalse(failed(inspect(self.skill()), strict=True))

    def test_missing_frontmatter(self):
        directory = self.skill()
        (directory / "SKILL.md").write_text("# No metadata", encoding="utf-8")
        self.assertIn("SP001", self.rules(directory))

    def test_unsafe_yaml_is_not_executed(self):
        directory = self.skill(front="!!python/object/apply:os.system ['exit 7']")
        self.assertIn("SP002", self.rules(directory))

    def test_duplicate_yaml_fields_rejected(self):
        self.assertIn("SP002", self.rules(self.skill(front="name: demo\nname: changed\ndescription: Example")))

    def test_non_string_yaml_keys_rejected(self):
        self.assertIn("SP002", self.rules(self.skill(front="1: demo\ndescription: Example")))

    def test_invalid_name_and_folder_mismatch(self):
        self.assertIn("SP003", self.rules(self.skill(front="name: Bad--Name\ndescription: Example")))
        other = self.skill("other", front="name: different\ndescription: Example")
        self.assertIn("SP004", self.rules(other))

    def test_description_type_and_length(self):
        for value in ["false", "''", "x" * 1025]:
            with self.subTest(value=value[:12]):
                directory = self.skill(parent=self.root / str(len(list(self.root.iterdir()))), front=f"name: demo\ndescription: {value}")
                self.assertIn("SP005", self.rules(directory))

    def test_optional_metadata_types(self):
        directory = self.skill(front="name: demo\ndescription: Useful documentation workflow.\nmetadata:\n  version: 1.0")
        self.assertIn("SP006", self.rules(directory))

    def test_host_extension_fields_preserved(self):
        directory = self.skill(front="name: demo\ndescription: Useful documentation workflow.\nallowed-tools: [Read, Grep]\nuser-invocable: true")
        self.assertFalse(failed(inspect(directory), strict=True))

    def test_empty_body_rejected(self):
        self.assertIn("SP007", self.rules(self.skill(body="")))

    def test_missing_and_escaped_links(self):
        directory = self.skill(body="[Missing](references/no.md)\n[Outside](../outside.md)")
        self.assertTrue({"SP009", "SP010"}.issubset(self.rules(directory)))

    def test_percent_encoded_traversal_rejected(self):
        self.assertIn("SP010", self.rules(self.skill(body="[Outside](%2e%2e/outside.md)")))

    def test_existing_resource_and_external_links(self):
        directory = self.skill(body="[Guide](references/guide.md)\n[Web](https://example.com/no.md)\n[Anchor](#heading)")
        (directory / "references").mkdir()
        (directory / "references/guide.md").write_text("# Guide", encoding="utf-8")
        self.assertFalse(failed(inspect(directory), strict=True))

    def test_parenthesized_resource_links_pass_check_and_pack(self):
        cases = [
            ("guide(v2).md", "[Guide](references/guide(v2).md)"),
            ("guide(v2(edited)).md", "[Guide](references/guide(v2(edited)).md)"),
            ("guide(v2).md", r"[Guide](references/guide\(v2\).md)"),
            ("guide(v2).md", '[Guide](references/guide(v2).md "Version 2")'),
            ("guide(v2).md", "[Guide](references/guide(v2).md 'Version 2')"),
            ("guide(v2).md", "[Guide](references/guide(v2).md (Version 2))"),
            ("guide v2).md", "[Guide](<references/guide v2).md>)"),
            ("figure(v2).png", "![Figure](references/figure(v2).png)"),
        ]
        for index, (filename, body) in enumerate(cases):
            with self.subTest(body=body):
                directory = self.skill(parent=self.root / str(index), body=body)
                (directory / "references").mkdir()
                (directory / "references" / filename).write_text("Example resource", encoding="utf-8")
                self.assertEqual(self.cli("check", directory, "--strict")[0], 0)
                if index == 0:
                    archive = self.root / "release.zip"
                    self.assertEqual(self.cli("pack", directory, "--output", archive)[0], 0)
                    with ZipFile(archive) as bundle:
                        self.assertIn("demo/references/guide(v2).md", bundle.namelist())

    def test_missing_parenthesized_resource_reports_complete_path(self):
        directory = self.skill(body="[Guide](references/missing(v2).md)")
        missing = [f for s in inspect(directory) for f in s.findings if f.rule == "SP009"]
        self.assertEqual([f.message for f in missing],
                         ["Missing local resource: references/missing(v2).md"])

    def test_unbalanced_parenthesized_destination_is_literal_text(self):
        directory = self.skill(body="[Not a link](references/guide(v2.md)")
        self.assertNotIn("SP009", self.rules(directory))

    def test_parenthesized_destination_still_rejects_outside_paths(self):
        self.assertIn("SP010", self.rules(self.skill(body="[Outside](../guide(v2).md)")))

    def test_fenced_example_links_ignored(self):
        directory = self.skill(body="```markdown\n[example](not-created.md)\n```\n\nActual instructions.")
        self.assertNotIn("SP009", self.rules(directory))

    def test_fence_with_trailing_text_does_not_close_code_block(self):
        for index, marker in enumerate(["```", "~~~"]):
            with self.subTest(marker=marker):
                directory = self.skill(
                    parent=self.root / str(index),
                    body=f"{marker}markdown\n{marker}python\n[Example](missing-example.md)\n{marker}\n\nActual instructions.",
                )
                self.assertEqual(self.cli("check", directory, "--strict")[0], 0)

    def test_links_after_real_fence_close_are_still_checked(self):
        for index, marker in enumerate(["```", "~~~"]):
            with self.subTest(marker=marker):
                actual_link = "[Actual](references/missing.md)"
                directory = self.skill(
                    parent=self.root / str(index),
                    body=f"{marker}markdown\n{marker}python\n[Example](missing-example.md)\n{marker}  \t\n\n{actual_link}",
                )
                file = directory / "SKILL.md"
                expected_line = file.read_text(encoding="utf-8").splitlines().index(actual_link) + 1
                missing = [f for s in inspect(directory) for f in s.findings if f.rule == "SP009"]
                self.assertEqual([(f.line, f.message) for f in missing],
                                 [(expected_line, "Missing local resource: references/missing.md")])

    def test_ignored_resource_link_rejected(self):
        directory = self.skill(body="[Cache](dist/example.md)")
        (directory / "dist").mkdir()
        (directory / "dist/example.md").write_text("Example", encoding="utf-8")
        self.assertIn("SP010", self.rules(directory))

    def test_sensitive_file_blocks_release(self):
        directory = self.skill()
        (directory / ".env").write_text("EXAMPLE=value", encoding="utf-8")
        skills = inspect(directory)
        self.assertTrue(failed(skills))
        with self.assertRaises(ValueError):
            pack(skills[0], self.root / "release.zip")

    def test_nested_markdown_links_checked(self):
        directory = self.skill()
        (directory / "references").mkdir()
        (directory / "references/guide.md").write_text("[Missing](missing.md)", encoding="utf-8")
        self.assertIn("SP009", self.rules(directory))

    def test_strict_and_json_report(self):
        directory = self.skill(body="# Work\n\nTODO explain output.")
        skills = inspect(directory)
        self.assertFalse(failed(skills))
        self.assertTrue(failed(skills, strict=True))
        data = json.loads(report(skills, "json"))
        self.assertEqual(data["errors"], 0)
        self.assertEqual(data["warnings"], 1)
        self.assertEqual(self.cli("check", directory, "--strict")[0], 1)

    def test_discover_hidden_host_folders_and_ignore_caches(self):
        directory = self.skill(parent=self.root / ".agents/skills")
        self.skill(parent=self.root / "node_modules")
        self.assertEqual(discover(self.root), [directory / "SKILL.md"])

    def test_no_skills_is_operational_error(self):
        self.assertEqual(self.cli("check", self.root)[0], 2)

    def test_pack_deterministic_and_excludes_cache(self):
        directory = self.skill()
        (directory / "__pycache__").mkdir()
        (directory / "__pycache__/cache.pyc").write_bytes(b"cache")
        (directory / "references").mkdir()
        (directory / "references/guide.md").write_text("# Guide", encoding="utf-8")
        skill = inspect(directory)[0]
        one, two = self.root / "one.zip", self.root / "two.zip"
        pack(skill, one)
        pack(skill, two)
        self.assertEqual(one.read_bytes(), two.read_bytes())
        with ZipFile(one) as archive:
            self.assertEqual(set(archive.namelist()), {"demo/SKILL.md", "demo/references/guide.md"})

    def test_pack_refuses_overwrite_and_inside_output(self):
        directory = self.skill()
        skill = inspect(directory)[0]
        output = self.root / "release.zip"
        pack(skill, output)
        original = output.read_bytes()
        with self.assertRaises(ValueError):
            pack(skill, output)
        self.assertEqual(original, output.read_bytes())
        with self.assertRaises(ValueError):
            pack(skill, directory / "inside.zip")

    def test_pack_collection_rejected(self):
        self.skill()
        self.assertEqual(self.cli("pack", self.root, "--output", self.root / "release.zip")[0], 2)

    def test_init_and_no_overwrite(self):
        self.assertEqual(self.cli("init", "write-docs", "--template", "docs", "--dir", self.root)[0], 0)
        original = (self.root / "write-docs/SKILL.md").read_bytes()
        self.assertEqual(self.cli("init", "write-docs", "--dir", self.root)[0], 2)
        self.assertEqual(original, (self.root / "write-docs/SKILL.md").read_bytes())
        self.assertEqual(self.cli("check", self.root, "--strict")[0], 0)

    def test_catalog_and_diagram(self):
        directory = self.skill()
        (directory / "references").mkdir()
        (directory / "references/guide.md").write_text("# Guide", encoding="utf-8")
        skills = inspect(directory)
        self.assertIn("| demo |", catalog(skills))
        self.assertIn("references/guide.md", diagram(skills))
        output = self.root / "docs/catalog.md"
        self.assertEqual(self.cli("docs", directory, "--output", output)[0], 0)
        self.assertTrue(output.exists())

    def test_duplicate_names_reported(self):
        self.skill(parent=self.root / "a")
        self.skill(parent=self.root / "b")
        self.assertIn("SP013", self.rules(self.root))

    def test_bom_and_windows_newlines(self):
        directory = self.skill()
        file = directory / "SKILL.md"
        file.write_bytes(b"\xef\xbb\xbf" + file.read_bytes().replace(b"\n", b"\r\n"))
        self.assertFalse(failed(inspect(directory)))

    def test_symlink_release_rejected(self):
        directory = self.skill()
        target = self.root / "outside.md"
        target.write_text("outside", encoding="utf-8")
        try:
            (directory / "linked.md").symlink_to(target)
        except OSError:
            self.skipTest("Symlink creation needs Windows developer mode or privileges")
        self.assertIn("SP011", self.rules(directory))


if __name__ == "__main__":
    unittest.main()
