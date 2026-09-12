import json
import subprocess
import unittest
from pathlib import Path
from scripts.p1_experiment_contract import EXPECTED_P1, DATASETS, validate

ROOT = Path(__file__).resolve().parents[1]


class CorrectP1MatrixTests(unittest.TestCase):
    def test_manifest_exact_user_list(self):
        manifest = json.loads((ROOT / "configs/p1_svc_multiimage.json").read_text())
        self.assertEqual(manifest["priority_1"], EXPECTED_P1)

    def test_user_output_budget_and_no_thinking(self):
        manifest = json.loads((ROOT / "configs/p1_svc_multiimage.json").read_text())
        self.assertEqual(manifest["generation"]["max_output_tokens"], 8192)
        self.assertEqual(manifest["generation"]["context_limit"], 65536)
        for model in manifest["models"].values():
            self.assertIs(model["enable_thinking"], False)
        pipeline = (ROOT / "scripts/p1_run_pipeline.sh").read_text()
        self.assertIn('export P1_VLM_MAX_TOKENS=8192', pipeline)
        self.assertIn('export QWEN_MAX_TOKENS=8192', pipeline)
        self.assertIn('export MINDJOURNEY_ENABLE_THINKING="false"', pipeline)
        submit = (ROOT / "scripts/p1_submit.sh").read_text()
        self.assertIn('P1_VLM_MAX_TOKENS=8192,QWEN_MAX_TOKENS=8192', submit)
        self.assertIn('"max_output_tokens=8192"', submit)

    def test_all_eight_shell_combinations(self):
        models = {"qwen35-27b": "Qwen/Qwen3.5-27B",
                  "qwen25vl-72b": "Qwen/Qwen2.5-VL-72B-Instruct",
                  "qwen35-9b": "Qwen/Qwen3.5-9B",
                  "qwen38-27b": "Qwen/Qwen3.8-27B"}
        for dataset, spec in DATASETS.items():
            for alias, model in models.items():
                with self.subTest(dataset=dataset, model=model):
                    result = subprocess.run(
                        ["bash", "-c", 'source "$1"; p1_load_model_spec "$2"; '
                         'p1_assert_priority_one_combo "$3"', "bash",
                         str(ROOT / "scripts/p1_model_registry.sh"), alias, dataset],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode == 0, model in spec["models"])

    def test_wrong_pairs_rejected_before_reading_files(self):
        for dataset, model in [("mindcube", "Qwen/Qwen3.5-27B"),
                               ("mmsi", "Qwen/Qwen3.5-9B")]:
            with self.assertRaisesRegex(ValueError, "NOT in the user's P1"):
                validate(dataset, model, "/missing", "/missing", 1000, 10)

    def test_wrong_size_rejected(self):
        with self.assertRaisesRegex(ValueError, "question count"):
            validate("mmsi", "Qwen/Qwen3.5-27B", "/missing", "/missing", 1050, 10)

    def test_contract_at_submission_and_before_loading(self):
        for file in ("p1_submit.sh", "p1_run_chunk.sh"):
            self.assertIn('p1_experiment_contract.py', (ROOT / "scripts" / file).read_text())
        self.assertIn('P1_GPU_MEMORY_UTILIZATION=0.93',
                      (ROOT / "scripts/p1_submit.sh").read_text())


if __name__ == "__main__":
    unittest.main()
