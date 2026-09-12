"""Test request semantics without importing OpenAI or any model runtime."""
import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class OutputBudgetTests(unittest.TestCase):
    def test_mixed_output_budget_rejected(self):
        from utils.p1_results import _validate_output_budget, P1ResultsError
        _validate_output_budget({"qwen_max_tokens": "8192"}, {"max_output_tokens": "8192"})
        with self.assertRaises(P1ResultsError):
            _validate_output_budget({"qwen_max_tokens": "1024"}, {"max_output_tokens": "8192"})

    def test_actual_config_and_request_kwargs(self):
        path = Path(__file__).resolve().parents[1] / "utils/api.py"
        tree = ast.parse(path.read_text())
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.Assign) and any(
                     isinstance(t, ast.Name) and t.id in
                     ("P1_MODEL_SPECS", "P1_MODEL_NAMES") for t in n.targets))
                 or (isinstance(n, ast.ClassDef) and n.name == "OpenAICompatibleConfig")]
        api = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ChatAPI")
        methods = [n for n in api.body if isinstance(n, ast.FunctionDef)
                   and n.name in ("_completion_kwargs", "_validate_no_thinking")]
        ns = {"os": os}
        exec(compile(ast.Module(body=nodes + methods, type_ignores=[]), str(path), "exec"), ns)
        with patch.dict(os.environ, {}, clear=True):
            for model in ns["P1_MODEL_NAMES"]:
                cfg = ns["OpenAICompatibleConfig"](model)
                request = ns["_completion_kwargs"](cfg, [])
                self.assertEqual(request["max_tokens"], 8192)
                if "Qwen2.5" in model:
                    self.assertNotIn("extra_body", request)
                else:
                    self.assertIs(request["extra_body"]["chat_template_kwargs"]["enable_thinking"], False)
                    with self.assertRaises(RuntimeError):
                        ns["_validate_no_thinking"](cfg, SimpleNamespace(reasoning_content="thinking"))
                    ns["_validate_no_thinking"](cfg, SimpleNamespace(content="Answer: B"))


if __name__ == "__main__":
    unittest.main()
