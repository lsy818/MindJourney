import copy
import json
from pathlib import Path
import tempfile
import unittest
from scripts.p1_resume_audit_fix import OLD_SOURCE, digest, prepare_checkpoint


class ResumeAuditFixTests(unittest.TestCase):
    def test_preserves_scores_rng_and_original_source(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path(directory) / "old"
            old.mkdir()
            new = Path(directory) / "new"
            group = dict(source_sha256=OLD_SOURCE, submitted_source_sha256=OLD_SOURCE,
                         qwen_max_tokens="8192", qwen_enable_thinking=False,
                         model_dtype="bfloat16", qwen_context_limit="65536")
            config = dict(run_group=group, output_dir=str(old), question_chunk_idx=0)
            original = dict(experiment=dict(configuration=config, fingerprint=digest(config),
                                            run_group_fingerprint=digest(group)),
                            progress={"type": {"correct": ["a"], "wrong": ["b"]}},
                            skip_indices=[], runtime_state={"python_random_state": [3, [1, 2], None]})
            (old / "results.json").write_text(json.dumps(original))
            unchanged = copy.deepcopy(original)
            result, ids = prepare_checkpoint(original, old, new, "f" * 64)
            self.assertEqual(original, unchanged)
            self.assertEqual(result["progress"], original["progress"])
            self.assertEqual(result["runtime_state"], original["runtime_state"])
            self.assertEqual(ids, ["a", "b"])
            self.assertEqual(result["resume_lineage"]["original_experiment"], original["experiment"])
            self.assertEqual(result["experiment"]["fingerprint"], digest(result["experiment"]["configuration"]))
            original["experiment"]["configuration"]["run_group"]["qwen_max_tokens"] = "1024"
            with self.assertRaises(ValueError):
                prepare_checkpoint(original, old, new, "f" * 64)


if __name__ == "__main__":
    unittest.main()
