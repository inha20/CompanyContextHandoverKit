import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from companytoai import cli  # noqa: E402


class HandoverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "h"
        cli.main(["init", str(self.dir)])

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_creates_all_required_files(self):
        for name in cli.REQUIRED:
            self.assertTrue((self.dir / name).exists(), name)

    def test_fresh_template_flags_todo(self):
        problems = cli.check_folder(self.dir, 30)
        self.assertTrue(any("TODO" in p for p in problems))

    def test_filled_folder_passes(self):
        for name in cli.REQUIRED:
            p = self.dir / name
            p.write_text(p.read_text(encoding="utf-8").replace("TODO", "내용"), encoding="utf-8")
        self.assertEqual(cli.check_folder(self.dir, 30), [])

    def test_stale_volatile_file_detected(self):
        for name in cli.REQUIRED:
            p = self.dir / name
            p.write_text(p.read_text(encoding="utf-8").replace("TODO", "내용"), encoding="utf-8")
        future = dt.date.today() + dt.timedelta(days=90)
        problems = cli.check_folder(self.dir, 30, today=future)
        self.assertTrue(any("02_current_status.md: stale" in p for p in problems))
        self.assertFalse(any("01_company_profile.md: stale" in p for p in problems))

    def test_build_pack_contains_documents_in_order(self):
        pack = cli.build_pack(self.dir)
        self.assertLess(pack.index("01_company_profile.md"), pack.index("08_changelog.md"))
        self.assertIn("문서에 없음", pack)

    def test_log_appends_and_updates_date(self):
        cli.main(["log", str(self.dir), "상황 갱신"])
        text = (self.dir / "08_changelog.md").read_text(encoding="utf-8")
        self.assertTrue(text.rstrip().endswith("상황 갱신"))

    def test_init_refuses_nonempty_dir(self):
        self.assertEqual(cli.main(["init", str(self.dir)]), 1)


if __name__ == "__main__":
    unittest.main()
