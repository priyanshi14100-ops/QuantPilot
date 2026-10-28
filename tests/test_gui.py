"""GUI smoke tests. Needs a display (on a headless machine run: xvfb-run python tests/test_gui.py)."""
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gui  # noqa: E402


class TestWindow(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError:
            self.skipTest("no display available (use xvfb-run on a headless machine)")
        self.app = gui.QuantPilotApp(self.root)
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_opens_with_sample_data_and_seven_tabs(self):
        self.assertEqual(len(self.app.stocks), 4)
        self.assertEqual(self.app.notebook.index("end"), 7)
        self.assertEqual(self.app.selected.get(), "ALPHA")
        self.assertNotEqual(self.app.stat_vars["Total Return %"].get(), "-")
        self.assertEqual(len(self.app.table.get_children()), len(self.app.stocks["ALPHA"]))

    def test_changing_stock_updates_statistics(self):
        before = self.app.stat_vars["Last Close"].get()
        self.app.selected.set("CHARLIE")
        self.app.update_selected()
        self.assertNotEqual(before, self.app.stat_vars["Last Close"].get())

    def test_upload_of_one_file(self):
        with tempfile.TemporaryDirectory() as folder:
            one = Path(folder) / "SOLO.csv"
            one.write_text(Path(gui.SAMPLE_DIR / "BRAVO.csv").read_text())
            self.app.load_files([one], "Uploaded files")
            self.assertEqual(list(self.app.stocks), ["SOLO"])
            self.assertEqual(self.app.selected.get(), "SOLO")

    def test_bad_file_keeps_old_data_and_names_missing_columns(self):
        shown = []
        gui.messagebox.showerror = lambda title, message: shown.append(message)
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "BAD.csv"
            bad.write_text("Date,Close\n2026-01-01,10\n")
            self.app.load_files([bad], "Uploaded files")
        self.assertEqual(len(self.app.stocks), 4)
        self.assertEqual(len(shown), 1)
        self.assertIn("Open", shown[0])
        self.assertIn("Volume", shown[0])

    def test_generate_report_fills_report_tab(self):
        path = self.app.generate_report(notify=False)
        self.assertTrue(path.exists())
        self.assertIn("ANALYTICAL REPORT", self.app.report_text.get("1.0", "end"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
