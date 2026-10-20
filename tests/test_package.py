import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackageTests(unittest.TestCase):
    def test_public_package_checks(self):
        checker = load("package_checker",ROOT / "tools/check_package.py")
        self.assertEqual(checker.check(),[])

    def test_release_is_standalone_and_reproducible(self):
        builder = load("release_builder",ROOT / "tools/build_release.py")
        with tempfile.TemporaryDirectory() as temp:
            a,ha = builder.build(Path(temp) / "a.zip")
            b,hb = builder.build(Path(temp) / "b.zip")
            self.assertEqual(ha,hb)
            with ZipFile(a) as archive:
                names = set(archive.namelist())
                self.assertIn("visual-story-production/SKILL.md",names)
                self.assertIn("visual-story-production/LICENSE.txt",names)
                self.assertIn("visual-story-production/assets/platform-adapter.md",names)
                self.assertIn("visual-story-production/scripts/validate_project.py",names)
                self.assertTrue(all(n.startswith("visual-story-production/") for n in names))
                self.assertFalse(any(".git/" in n or "__pycache__" in n or "examples/" in n for n in names))

    def test_validator_has_no_network_or_external_import(self):
        import ast
        tree=ast.parse((ROOT / "skills/visual-story-production/scripts/validate_project.py").read_text(encoding="utf-8"))
        imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                imports.extend(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node,ast.ImportFrom):
                imports.append(node.module.split('.')[0])
        self.assertTrue(set(imports) <= {"__future__","argparse","json","math","pathlib","sys"},imports)
