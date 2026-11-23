"""UI integration checks; pointer/keyboard interactions also need browser QA."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=30).run()

    def test_input_error_recovery_and_reset(self):
        a = self.app
        self.assertFalse(a.exception)
        a.number_input(key="x").set_value(120.0)
        a.number_input(key="y").set_value(36.0).run()
        self.assertIn("goalpost", a.error[0].value)
        a.button[0].click().run()
        self.assertFalse(a.error)
        self.assertEqual(a.number_input(key="x").value, 108.0)
        a.selectbox(key="body_part").select("Head").run()
        self.assertEqual(set(a.selectbox(key="technique").options), {"Normal", "Diving Header"})
        self.assertFalse(a.exception)

    def test_navigation_evidence_and_guide(self):
        a = self.app
        a.segmented_control[0].set_value("Model evidence").run()
        self.assertFalse(a.exception)
        self.assertEqual(len(a.dataframe), 2)
        a.radio[0].set_value("test").run()
        self.assertIn("retrospective", a.warning[0].value)
        a.segmented_control[0].set_value("Project guide").run()
        self.assertFalse(a.exception)
        self.assertTrue(any("not deep learning" in m.value for m in a.markdown))
        a.segmented_control[0].set_value(None).run()
        self.assertEqual(a.title[0].value, "Understand the shot.")


if __name__ == "__main__":
    unittest.main()
