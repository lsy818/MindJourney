from utils.vlm_wrapper import VLMWrapper
from utils.prompt_formatting import SYS, BASELINE_PROMPT
from utils.answer_parsing import score_multiple_choice_response
from tqdm import tqdm
import argparse
import hashlib
import json
import random
import os
import cv2
import sys
from utils.args import get_svc_args
from decord import VideoReader, cpu
import math
import numpy as np
from scipy.spatial.transform import Rotation as R
import pickle
from diffusers.utils import export_to_video
import copy

def resize_to_short_side(img, target_short=512):
    h, w = img.shape[:2]
    if min(h, w) == target_short:          # already the right size
        return img
    scale = target_short / float(min(h, w))
    new_w, new_h = int(math.ceil(w * scale)), int(math.ceil(h * scale))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    return cv2.resize(img, (new_w, new_h), interpolation=interp)

class ActionSpace:
    MOVE_FORWARD = 1
    TURN_LEFT = 2
    TURN_RIGHT = 3

class PipelineBase:

    @staticmethod
    def _sha256_file(path):
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _stage_source_images(self, question, save_dir):
        """Stage every source image without changing its benchmark order.

        Image 1 remains the sole conditioning image for SVC.  The returned
        ordered list is passed in full to the VLM, so auxiliary benchmark views
        are never silently dropped.
        """

        source_paths = list(question.get("img_paths") or [])
        if not source_paths:
            raise ValueError(
                f"Question {question.get('database_idx')} has no source images."
            )

        step_dir = os.path.join(save_dir, "step_0")
        os.makedirs(step_dir, exist_ok=True)
        staged_paths = []
        order_manifest = []
        for index, source_path in enumerate(source_paths):
            image = cv2.imread(source_path)
            if image is None:
                raise FileNotFoundError(
                    f"Could not decode source image {index + 1}: {source_path}"
                )
            if self.model_args.vlm_model_name == "OpenGVLab/InternVL3-14B":
                image = cv2.resize(image, (512, 512), interpolation=cv2.INTER_LINEAR)
            else:
                image = resize_to_short_side(image, target_short=512)
            filename = "img_0.png" if index == 0 else f"helper_img_{index:03d}.png"
            staged_path = os.path.join(step_dir, filename)
            if not cv2.imwrite(staged_path, image):
                raise OSError(f"Could not write staged image: {staged_path}")
            staged_paths.append(staged_path)
            order_manifest.append(
                {
                    "image_number": index + 1,
                    "source_path": source_path,
                    "source_sha256": self._sha256_file(source_path),
                    "staged_path": staged_path,
                }
            )

        with open(os.path.join(step_dir, "source_image_order.json"), "w") as handle:
            json.dump(order_manifest, handle, indent=2)
        return staged_paths

    def _build_experiment_record(self, input_file):
        """Fingerprint the exact code, data, model, and launch configuration."""

        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source_digest = hashlib.sha256()
        for source_root in ("pipelines", "utils", "stable_virtual_camera"):
            absolute_root = os.path.join(repo_root, source_root)
            for directory, dirnames, filenames in os.walk(absolute_root):
                dirnames.sort()
                for filename in sorted(filenames):
                    if not filename.endswith(".py"):
                        continue
                    path = os.path.join(directory, filename)
                    source_digest.update(os.path.relpath(path, repo_root).encode())
                    with open(path, "rb") as handle:
                        source_digest.update(handle.read())

        source_sha256 = source_digest.hexdigest()
        expected_source = os.environ.get("MINDJOURNEY_EXPECTED_SOURCE_SHA256")
        if expected_source and source_sha256 != expected_source:
            raise RuntimeError(
                "Python source differs from the hash pinned at formal submission."
            )

        arguments = dict(vars(self.model_args))
        common_arguments = {
            key: value
            for key, value in arguments.items()
            if key not in {"output_dir", "question_chunk_idx"}
        }
        manifest_path = os.environ.get("MINDJOURNEY_EXPERIMENT_MANIFEST")
        provenance_path = os.environ.get("MINDJOURNEY_DATASET_PROVENANCE")
        common = {
            "arguments": common_arguments,
            "dataset_json_sha256": self._sha256_file(input_file),
            "dataset_provenance_sha256": (
                self._sha256_file(provenance_path)
                if provenance_path and os.path.isfile(provenance_path)
                else None
            ),
            "manifest_sha256": (
                self._sha256_file(manifest_path)
                if manifest_path and os.path.isfile(manifest_path)
                else None
            ),
            "source_sha256": source_sha256,
            "submitted_source_sha256": expected_source,
            "model_revision": os.environ.get("QWEN_REVISION"),
            "model_tree_sha256": os.environ.get("MINDJOURNEY_MODEL_TREE_SHA256"),
            "model_dtype": os.environ.get("MINDJOURNEY_MODEL_DTYPE", "bfloat16"),
            "qwen_enable_thinking": os.environ.get(
                "MINDJOURNEY_ENABLE_THINKING", "false"
            ).lower()
            == "true",
            "qwen_context_limit": os.environ.get("QWEN_CONTEXT_LIMIT"),
            "qwen_max_tokens": os.environ.get("QWEN_MAX_TOKENS"),
            "vllm_version": os.environ.get("QWEN_VLLM_VERSION"),
            "svc_revision": os.environ.get("SVC_REVISION"),
            "svc_weight_sha256": os.environ.get("SVC_WEIGHT_SHA256"),
            "svc_strict_load": os.environ.get("SVC_STRICT_LOAD"),
            "runtime_environment": os.environ.get("MINDJOURNEY_ENV_ID"),
            "hardware": os.environ.get("MINDJOURNEY_HARDWARE"),
            "protocol": "paper-aligned SVC multi-image adaptation",
        }
        common_json = json.dumps(common, sort_keys=True, separators=(",", ":"))
        run_group_fingerprint = hashlib.sha256(common_json.encode()).hexdigest()
        configuration = {
            "run_group": common,
            "output_dir": arguments["output_dir"],
            "question_chunk_idx": arguments["question_chunk_idx"],
        }
        chunk_json = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
        return {
            "fingerprint": hashlib.sha256(chunk_json.encode()).hexdigest(),
            "run_group_fingerprint": run_group_fingerprint,
            "configuration": configuration,
        }

    def __init__(
        self,
    ):  
        self.world_model_type = os.getenv('WORLD_MODEL_TYPE')
        self.question_database_type = os.getenv('QUESTION_DATABASE_TYPE')
        self.model_args = get_svc_args()
        print("model_args:", self.model_args)
        self.prompt = BASELINE_PROMPT

        num_questions = self.model_args.num_questions
        
        if self.model_args.question_type == "None":
            input_file = os.path.join(self.model_args.input_dir, f"{self.model_args.split}.json")
        else:
            input_file = os.path.join(self.model_args.input_dir, f"{self.model_args.split}_{self.model_args.question_type}.json")
        if self.model_args.scaling_strategy is not None:
            self.model_args.output_dir += f"_{self.model_args.scaling_strategy}"
            os.makedirs(self.model_args.output_dir, exist_ok=True)
        if self.model_args.num_question_chunks > 1:
            self.model_args.output_dir += f"_qc{self.model_args.num_question_chunks}"
            os.makedirs(self.model_args.output_dir, exist_ok=True)
            self.model_args.output_dir = os.path.join(self.model_args.output_dir, f"question_chunk_{self.model_args.question_chunk_idx}")
            os.makedirs(self.model_args.output_dir, exist_ok=True)

        self.questions = self.select_questions(input_file, seed=10, num_questions=num_questions)
        self.num_underlying_questions = len(self.questions)
        if self.model_args.num_question_chunks > 1:
            idx = self.model_args.question_chunk_idx
            total = self.model_args.num_question_chunks

            print(f"chunk index: {idx}")
            assert 0 <= idx < total, f"Invalid chunk index: {idx}"

            total_questions = len(self.questions)
            chunk_size = total_questions // total
            start = idx * chunk_size
            end = total_questions if idx == total - 1 else (start + chunk_size)

            self.questions = self.questions[start:end]
        self.question_type_list = self.get_question_type_list()
        self.vlm = VLMWrapper(model_name=self.model_args.vlm_model_name, qa_model_name=self.model_args.vlm_qa_model_name)
        experiment_record = self._build_experiment_record(input_file)

        # ================== NEW OR MODIFIED BEGIN ==================
        if os.path.exists(os.path.join(self.model_args.output_dir, f"results.json")):
            with open(os.path.join(self.model_args.output_dir, f"results.json"), 'r') as f:
                self.results = json.load(f)
            if self.results.get("experiment", {}).get("fingerprint") != experiment_record["fingerprint"]:
                raise RuntimeError(
                    "Existing results.json belongs to a different experiment. "
                    "Use a new output directory."
                )
        else:
            self.results = {
                "experiment": experiment_record,
                "evaluation": {
                    "underlying_questions": self.num_underlying_questions,
                    "evaluated_in_chunk": len(self.questions),
                    "aggregation": "top1_accuracy_over_questions",
                },
                "current": None,
                "parsing_err_stats":{
                    "scores": 0,
                    "answer": 0,
                    "answer_qid": [],
                    "scores_qid": [],
                },
                "accuracy": {
                    "all": None,
                    "types" : {
                        question_type: None for question_type in self.question_type_list
                    }
                },
                "skip_indices": [],
                "progress":{
                    question_type: {
                        "correct": [],
                        "wrong": [],
                    } for question_type in self.question_type_list
                
                }
            }
            # self.save_results()

    def get_question_type_list(self):
        """
        Scan the question type and return the corresponding type.
        """
        question_type_list = []
        for question in self.questions:
            question_type = question["question_type"]
            if question_type not in question_type_list:
                question_type_list.append(question_type)
        return question_type_list
    def _process_bbox(self, response: str):
        """Parse LLM response to a bounding box: [(x1,y1), (x2,y2)]. response is in format (150,160):(180,220)."""
        try:
            if "Output:" in response:
                response = response.split("Output:")[1]
            list_= []
            coordinates = response.split(":")
            for coordinate in coordinates:
                coordinate = coordinate.strip()[1:-1].split(',')
                list_.append((int(coordinate[0]), int(coordinate[1])))
            return list_
        except Exception:
            pass
        return "out of control"
    def save_results(self):
        """Save results to JSON file."""
        result_path = os.path.join(self.model_args.output_dir, "results.json")
        temp_path = result_path + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(self.results, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, result_path)
        # ================== NEW OR MODIFIED END ==================

    def run(self):

        for question in tqdm(self.questions):
            qid = question["eval_id"] if "eval_id" in question else question["database_idx"]
            # ------------------------------------------------------------------
            #  Quick filters & deduplication
            # ------------------------------------------------------------------
            if question["question_type"] in ["other"]:
                self.results["skip_indices"].append(qid)
                continue

            if len(question["img_paths"]) > self.model_args.max_images:
                print(f"[SpatialVQA] Skipping question {question['database_idx']} - only one image supported.")
                self.results["skip_indices"].append(qid)
                self.save_results()
                continue

            if (
                qid in self.results["skip_indices"]
                or any(qid in result["correct"] for result in self.results["progress"].values())
                or any(qid in result["wrong"] for result in self.results["progress"].values())
            ):
                print(f"[SpatialVQA] Skipping already processed question {qid}.")
                continue

            os.makedirs(os.path.join(self.model_args.output_dir, f"{qid}"), exist_ok=True)

            # ------------------------------------------------------------------
            #  Set-up per-question output folder & initial image(s)
            # ------------------------------------------------------------------
            save_dir = os.path.join(self.model_args.output_dir, f"{qid}")

            os.makedirs(os.path.join(save_dir, f"step_0"), exist_ok=True)

            source_image_paths = self._stage_source_images(question, save_dir)
            primary_img_path = source_image_paths[0]

            # ------------------------------------------------------------------
            #  Dialogue loop (LLM <-> environment)
            # ------------------------------------------------------------------
            response, result, action_list, magnitude = None, "out of control", [], None
            for step in range(self.model_args.max_steps_per_question):
                print(f"\n[SpatialVQA] ===== Step {step} for QID {qid} =====")

                for _ in range(self.model_args.max_tries_gpt):
                    sys_prompt, content = self.vlm.format_prompt(prompt_type="answer_baseline",
                        question=question["question"],
                        answer_choices=question["answer_choices"],
                        images=source_image_paths,
                    )
                    response = self.vlm.run_prompt("answer_baseline", sys_prompt, content)
                    print("[LLM]", response)
                    result = self._process_answer(response, question)
                    if result != "out of control":
                        break

                self._dump_llm_interaction(save_dir, step, question, response, result, None, None)
                if result == "out of control":
                    result = "wrong"

                if result in ("correct", "wrong"):
                    self.results["progress"][question["question_type"]][result].append(qid)
                    break

                print(f"===============End of iteration {step}================")

            print("result:", result)
            
            # ----------------------------------------------------------
            #  Terminal answer?  –> store + break
            # ----------------------------------------------------------

            all_types = self.results["progress"].keys()
            correct_total = sum(len(self.results["progress"][t]["correct"]) for t in all_types)
            wrong_total = sum(len(self.results["progress"][t]["wrong"]) for t in all_types)
            self.results["accuracy"]["all"] = correct_total / (correct_total + wrong_total)
            for t in all_types:
                if len(self.results["progress"][t]["correct"]) + len(self.results["progress"][t]["wrong"]) != 0:
                    self.results["accuracy"]["types"][t] = len(self.results["progress"][t]["correct"]) / (
                        len(self.results["progress"][t]["correct"]) + len(self.results["progress"][t]["wrong"])
                    )
                else:
                    self.results["accuracy"]["types"][t] = None
            self.save_results()

    def load_skips(self, skip_file):
        if os.path.exists(skip_file):
            with open(skip_file, 'r') as f:
                return json.load(f)
        else:
            return []


    def save_skips(self):
        with open(self.skip_file, 'w') as f:
            json.dump(self.skip_indices, f, indent=4)

    def calculate_types_count(results):
        count_map = {
            'correct': [],
            'wrong': [],
        }
        for result in results:
            if result in count_map.keys():
                count_map[result] += 1
        return count_map

    def select_questions(self, input_file, seed=None, num_questions=1):
        """
        Select a specified number of questions from a JSON file using a custom seed.

        :param input_file: Path to the JSON file containing a list of questions
        :param seed: Custom seed for random number generation (int or None)
        :param num_questions: Number of questions to select
        :return: List of selected questions
        """
        with open(input_file, 'r') as f:
            all_questions = json.load(f)

        # Set the random seed (if None, it won't fix the seed)
        random.seed(seed)

        # Ensure we don't request more questions than are available
        num_to_select = min(num_questions, len(all_questions))

        # Use random.sample to select multiple distinct items
        selected = random.sample(all_questions, k=num_to_select)
        return selected

    def init_prompt(self, question):
        self.chat_api.message = [
            {"role": "system", "content": SYS},
        ]
        new_prompt = self.prompt.format(
                question=question['question'], 
                answer_choice=question['answer_choices']
            )
        self.chat_api.add_user_image_message(
            question["img_paths"], 
            new_prompt
        )
        return new_prompt
    def _dump_llm_interaction(self, save_dir, step, question, response, result, actions, magnitude):
        prompt = copy.deepcopy(self.vlm.curr_prompt)
        log = {
            "question": question,
            "result": result,
            "action_list": actions,
            "magnitude": magnitude,
            "llm_response": response,
            "prompt": prompt,
        }
        step_dir = os.path.join(save_dir, f"step_{step}")
        os.makedirs(step_dir, exist_ok=True)
        with open(os.path.join(step_dir, "gpt.json"), "w") as f:
            json.dump(log, f, indent=2)

    def _process_answer(self, response: str, question: dict, fwd=0.075, turn=3):
        """Parse LLM response and map to (result, actions, magnitude)."""
        try:
            return score_multiple_choice_response(response, question)
        except Exception:
            pass
        return "out of control"

if __name__ == "__main__":
    pipeline = PipelineBase()
    pipeline.run()
