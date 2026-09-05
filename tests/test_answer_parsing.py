import unittest

from utils.answer_parsing import extract_answer_label, score_multiple_choice_response


class AnswerParsingTests(unittest.TestCase):
    def test_explicit_label_and_exact_text_are_supported(self):
        choices = ["A: left of the chair", "B: right of the chair"]
        self.assertEqual(
            extract_answer_label("brief analysis\nAnswer: B", choices), "B"
        )
        self.assertEqual(extract_answer_label("right of the chair", choices), "B")
        self.assertEqual(extract_answer_label("The answer is **B**", choices), "B")
        self.assertEqual(extract_answer_label(r"\boxed{B}", choices), "B")

    def test_substrings_and_ambiguous_duplicate_text_are_rejected(self):
        self.assertIsNone(
            extract_answer_label("red box", ["A: box", "B: red box near chair"])
        )
        self.assertIsNone(extract_answer_label("same", ["A: same", "B: same"]))

    def test_score_prefers_dataset_answer_letter(self):
        question = {
            "answer_choices": ["A. one", "B. two"],
            "correct_answer": "two",
            "correct_answer_letter": "B",
        }
        self.assertEqual(score_multiple_choice_response("Answer: B", question), "correct")
        self.assertEqual(score_multiple_choice_response("Answer: A", question), "wrong")
