"""Frozen SVC search loop with raw/marked routing and offline-only scoring.
Search/selection/generation are inherited without budget changes.
"""
from pipeline_svc_scaling_spatial_beam_search import SpatialVQAPipelineSVC, ActionSpace
import os, random

class Search(SpatialVQAPipelineSVC):
    def run(self) -> None:
        """Main evaluation loop (mirrors the logic of the original script)."""
        for question in self.questions:
            qid = question["eval_id"] if "eval_id" in question else question["database_idx"]
            # ------------------------------------------------------------------
            #  Quick filters & deduplication
            # ------------------------------------------------------------------
            if question["question_type"] in ["other"]:
                print(f"[SpatialVQA] Skipping question {question['database_idx']} - not a spatial VQA task.")
                self.results["skip_indices"].append(qid)
                self.save_results()
                continue

            if self.model_args.question_type != "None" and question["question_type"] != self.model_args.question_type:
                print(f"[SpatialVQA] Skipping question {question['database_idx']} - not a {self.model_args.question_type} task.")
                self.results["skip_indices"].append(qid)
                self.save_results()
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
            primary_img_path = self.raw_staged  # raw RGB only conditions SVC

            # ------------------------------------------------------------------
            #  Dialogue loop (LLM <-> environment)
            # ------------------------------------------------------------------
            response, result, action_list, magnitude = None, "out of control", [], None
            previous_action_sequences = None
            previous_action_lists = None
            helpful_action_consequences = {}
            system_prompts_for_double_search = [
                (
                    "Task: You are an AI assistant designed to help with spatial reasoning in a 3D indoor scene. "
                    "You must analyze any provided images and score imagined images based on how suitable they are for exploring these action consequences in order to answer the question from the choices.\n\n"
                    "Rules:\n"
                    "1. You'll be provided with images (including imagined images), a question, and a set of answer choices. You should score all imagined images.\n"
                    "2. You should output a list of scores from 0 to 9, separated by ','. For example: Output: 3,5,2,9,0,1\n"
                ),
                (
                    "Task: You are an AI assistant designed to help with spatial reasoning in a 3D indoor scene. "
                    "You must analyze any provided images and score imagined images based on how helpful they are for answering the questions.\n\n"
                    "Hint: They may not be correct for answering the questions, but they will be helpful for excluding the wrong answers. The scores should also consider the image quality. If the image quality is very bad, it should receive a low score. Otherwise, the score should be augmented.\n\n"
                    "Rules:\n"
                    "1. You'll be provided with images (including imagined images), a question, and a set of answer choices. You should score all imagined images.\n"
                    "2. You should output a list of scores from 0 to 9, separated by ','. For example: Output: 3,5,2,9,0,1\n"
                )
            ]
            for step in range(self.model_args.max_steps_per_question):
                print(f"\n[SpatialVQA] ===== Step {step} for QID {qid} =====")

                # ----------------------------------------------------------
                #  Query World Model - simulate all actions
                # ----------------------------------------------------------
                top_scores = []
                helpful_store = []
                print("previous_action_sequences", previous_action_sequences)
                print("previous_action_lists", previous_action_lists)
                possible_actions = [f"move-forward {self.model_args.fixed_forward_magnitudes}", f"turn-left {self.model_args.fixed_rotation_magnitudes}", f"turn-right {self.model_args.fixed_rotation_magnitudes}"]
                action_candidates = self._simulate_all_actions(
                    image_path=primary_img_path,
                    step_idx=step,
                    actions=possible_actions,         # e.g. ["move-forward 0.75", "turn-left 30", "turn-right 30"]
                    sampling_interval_angle=self.model_args.sampling_interval_angle,
                    sampling_interval_meter=self.model_args.sampling_interval_meter,
                    model_args=self.model_args,
                    save_dir=save_dir,
                    previous_action_sequences=previous_action_sequences if previous_action_sequences is not None else None,
                    previous_action_lists=previous_action_lists if previous_action_lists is not None else None,
                )
                temp_actions_store = []
                for action_str, subaction_consequences in action_candidates.items():
                    for subaction_str, img_path in subaction_consequences.items():
                        temp_actions_store.append((action_str, subaction_str, img_path))
                if len(temp_actions_store) == 0:
                    print("No action candidates found. Goes to Q&A.")
                    break
                # print("number of action candidates:", len(temp_actions_store))
                top_scores_all = [None, None]
                for rank_i in range(2):
                    for _ in range(self.model_args.max_tries_gpt):
                        sys_prompt, content = self.vlm.format_prompt(prompt_type="prompt_scores",
                            question=question["question"],
                            answer_choices=question["answer_choices"],
                            images=source_image_paths,
                            action_consequences=temp_actions_store,
                            sys_prompt=system_prompts_for_double_search[rank_i],
                        )
                        response = self.vlm.run_prompt("prompt_scores", sys_prompt, content)
                        print("[LLM RESPONSE in choose n]", response)
                        scores = self._process_list(response)
                        if scores != "out of control" and len(scores) != len(temp_actions_store):
                            print(
                                "[WARN] Score count mismatch: "
                                f"expected {len(temp_actions_store)}, got {len(scores)}."
                            )
                            scores = "out of control"
                        # print("[RESULT after process]", scores)
                        if scores != "out of control":
                            break
                    self._dump_llm_interaction(save_dir, step, rank_i, question, response, result, action_list, magnitude)
                    # save top indexes and corresponding scores to top_candidates (scores are unsorted, ranked by index)
                    # in the format of [(index, score), ...]
                    if scores != "out of control":
                        top_scores_all[rank_i] = [(score, index) for index, score in enumerate(scores)]
                        top_scores_all[rank_i].sort(key=lambda x: x[0], reverse=True)
                    else:
                        self.results["parsing_err_stats"]["scores"] += 1
                        if rank_i == 1:
                            self.results["parsing_err_stats"]["scores_qid"].append(qid)
                        scores = [random.randint(0, 5) for _ in range(len(temp_actions_store))]
                        print("sampled scores:", scores)
                        top_scores_all[rank_i] = [(score, index) for index, score in enumerate(scores)]
                        top_scores_all[rank_i].sort(key=lambda x: x[0], reverse=True)
                    # Add to helpful action consequences, which had the same format as action_candidates
                    if rank_i == 1:
                        for score, index in top_scores_all[rank_i]:
                            if index >= len(temp_actions_store):
                                print("index out of range")
                                continue
                            action_str, subaction_str, img_path = temp_actions_store[index]
                            # if score is smaller than 6, skip
                            if score < self.model_args.helpful_score_threshold:
                                continue
                            if img_path not in [helpful[3] for helpful in helpful_store]:
                                helpful_store.append((score, action_str, subaction_str, img_path))
                
                previous_action_sequences = []
                previous_action_lists = []
                for score, index in top_scores_all[0][:self.model_args.num_beams]:
                    if index >= len(temp_actions_store):
                        print("index out of range")
                        continue
                    if score < self.model_args.exploration_score_threshold:
                        continue
                    action_str, subaction_str, img_path = temp_actions_store[index]
                    previous_action_list = []
                    previous_action_sequence = []
                    raw_extracted_previous_action_sequence = subaction_str.split(", and then ")[0].split(", ")
                    if ", and then " in subaction_str:
                        raw_extracted_previous_action_sequence.append(subaction_str.split(", and then ")[1])
                    for raw_action in raw_extracted_previous_action_sequence:
                        magnitude = float(raw_action.split(" ")[-2])
                        if "move forward" in raw_action:
                            num_steps = round(magnitude / self.model_args.sampling_interval_meter)
                            for _ in range(num_steps):
                                previous_action_list.append(ActionSpace.MOVE_FORWARD)
                            previous_action_sequence.append(raw_action.replace("move forward", "move-forward"))
                        elif "turn left" in raw_action:
                            num_steps = round(magnitude / self.model_args.sampling_interval_angle)
                            for _ in range(num_steps):
                                previous_action_list.append(ActionSpace.TURN_LEFT)
                            previous_action_sequence.append(raw_action.replace("turn left", "turn-left"))
                        elif "turn right" in raw_action:
                            num_steps = round(magnitude / self.model_args.sampling_interval_angle)
                            for _ in range(num_steps):
                                previous_action_list.append(ActionSpace.TURN_RIGHT)
                            previous_action_sequence.append(raw_action.replace("turn right", "turn-right"))
                    previous_action_sequences.append(previous_action_sequence)
                    previous_action_lists.append(previous_action_list)
                # sort helpful_store by score
                helpful_store.sort(key=lambda x: x[0], reverse=True)
                number_of_successful_additions = 0
                for score, action_str, subaction_str, img_path in helpful_store:
                    if number_of_successful_additions < self.model_args.num_top_candidates:
                        if action_str not in helpful_action_consequences:
                            helpful_action_consequences[action_str] = {}
                        if subaction_str not in helpful_action_consequences[action_str]:
                            helpful_action_consequences[action_str][subaction_str] = img_path
                            number_of_successful_additions += 1
                    else:
                        break
            
            for action_str, subaction_consequences in helpful_action_consequences.items():
                # please determine the last image by the order of the subaction's magnitude
                subaction_consequences = sorted(subaction_consequences.items(), key=lambda x: float(x[0].split(" ")[-2]))
                helpful_action_consequences[action_str] = dict(subaction_consequences)

            # ----------------------------------------------------------
            #  Query LLM - allow a few retries if response unparsable
            # ----------------------------------------------------------
            number_of_imaginations = 0
            for action_str in helpful_action_consequences.keys():
                number_of_imaginations += len(helpful_action_consequences[action_str])
            print("Number of imaginations:", number_of_imaginations)
            for _ in range(self.model_args.max_tries_gpt):
                sys_prompt, content = self.vlm.format_prompt(prompt_type="answer_scaling",
                    question=question["question"],
                    answer_choices=question["answer_choices"],
                    images=source_image_paths,
                    action_consequences=helpful_action_consequences,
                )
                response = self.vlm.run_prompt("answer_scaling", sys_prompt, content)
                print("[LLM RESPONSE]", response)
                result = self._process_answer(response, question)
                # print("[RESULT After Process]", result)
                if result != "out of control":
                    break
            
            # Persist raw exchange for debugging / auditing
            self._dump_llm_interaction(save_dir, None, None, question, response, result, action_list, magnitude)

            self.save_prediction(question, response, number_of_imaginations)
