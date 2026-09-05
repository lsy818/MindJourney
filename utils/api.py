from openai import AzureOpenAI, OpenAI
from typing import Dict, List
import logging
import base64
import os


# Immutable Hugging Face revisions used by the priority-one runs.  Keep this
# table in sync with scripts/p1_model_registry.sh: the Python side controls the
# request semantics while the shell side controls the vLLM process and Slurm
# resources.
P1_MODEL_SPECS = {
    "Qwen/Qwen3.5-27B": {
        "revision": "fc05daec18b0a78c049392ed2e771dde82bdf654",
        "enable_thinking": False,
    },
    "Qwen/Qwen2.5-VL-72B-Instruct": {
        "revision": "89c86200743eec961a297729e7990e8f2ddbc4c5",
        # Qwen2.5-VL has no compatible enable_thinking chat-template option.
        "enable_thinking": None,
    },
    "Qwen/Qwen3.5-9B": {
        "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "enable_thinking": False,
    },
    "Qwen/Qwen3.8-27B": {
        "revision": "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0",
        "enable_thinking": False,
    },
}
P1_MODEL_NAMES = tuple(P1_MODEL_SPECS)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

logger = logging.getLogger(__name__)
class AzureConfig:
    def __init__(self, api_model, api_version="2024-12-01-preview", api_price=0.01):
        self.api_type = "azure"
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.api_version = api_version
        self.azure_endpoint = "YOUR_API_ENDPOINT"
        self.model = api_model
        self.limit = 30000
        self.price = api_price
        self.temperature = None
        self.top_p = None
        if self.model not in ["o4-mini", "o1"]:
            self.temperature = 0.00000001
            self.top_p = 0.0


class OpenAICompatibleConfig:
    """Configuration for a pinned local vLLM multimodal endpoint.

    All priority-one models use deterministic BF16 serving with a 65,536-token
    context.  Thinking is disabled only for Qwen3-family models.  In
    particular, no thinking-related request field is sent to Qwen2.5-VL.
    """

    def __init__(self, api_model):
        try:
            model_spec = P1_MODEL_SPECS[api_model]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported OpenAI-compatible model {api_model!r}; "
                f"expected one of {', '.join(P1_MODEL_NAMES)}."
            ) from exc

        self.api_type = "openai_compatible"
        self.api_key = os.environ.get(
            "P1_VLM_API_KEY", os.environ.get("QWEN_API_KEY", "EMPTY")
        )
        self.base_url = os.environ.get(
            "P1_VLM_API_BASE",
            os.environ.get("QWEN_API_BASE", "http://127.0.0.1:8000/v1"),
        )
        self.model = api_model
        self.revision = model_spec["revision"]
        self.limit = 65536
        self.price = 0.0
        self.temperature = 0.0
        self.top_p = 1.0
        self.max_tokens = int(
            os.environ.get(
                "P1_VLM_MAX_TOKENS", os.environ.get("QWEN_MAX_TOKENS", "1024")
            )
        )
        if self.max_tokens <= 0:
            raise ValueError("P1_VLM_MAX_TOKENS must be a positive integer.")

        enable_thinking = model_spec["enable_thinking"]
        self.extra_body = None
        self.require_no_thinking = False
        if enable_thinking is False:
            self.extra_body = {
                "chat_template_kwargs": {"enable_thinking": False},
            }
            self.require_no_thinking = True
        self.fail_fast = True

class ChatAPI:
    def __init__(
        self,
        config: AzureConfig,
    ):
        self.messages: List[Dict[str, str]] = []
        self.history: List[Dict[str, str]] = []

        if config.api_type == "azure":
            self.client = AzureOpenAI(
                api_key=config.api_key,
                api_version=config.api_version,
                azure_endpoint=config.azure_endpoint,
            )
        elif config.api_type == "openai_compatible":
            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
            )
        else:
            raise ValueError(f"Unsupported API type: {config.api_type}")

        self.model = config.model
        self.max_limit = min(config.limit - 2000, 20000)
        self.price = config.price
        self.usage_tokens = 0
        self.cost = 0  # USD money cost
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.max_tokens = getattr(config, "max_tokens", None)
        self.extra_body = getattr(config, "extra_body", None)
        self.require_no_thinking = getattr(config, "require_no_thinking", False)
        self.fail_fast = getattr(config, "fail_fast", False)

    def _completion_kwargs(self, messages, stream=False):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "seed": 44,
        }
        if self.temperature is not None and self.top_p is not None:
            kwargs.update(temperature=self.temperature, top_p=self.top_p)
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        # Deliberately omitted for Qwen2.5-VL, whose chat template does not
        # accept Qwen3's enable_thinking keyword.
        if self.extra_body is not None:
            kwargs["extra_body"] = self.extra_body
        if stream:
            kwargs["stream"] = True
        return kwargs

    def _validate_no_thinking(self, response_message):
        if not self.require_no_thinking:
            return
        for field in ("reasoning", "reasoning_content"):
            reasoning = getattr(response_message, field, None)
            if reasoning and str(reasoning).strip():
                raise RuntimeError(
                    f"{self.model} returned non-empty {field}; "
                    "the no-thinking setting was not applied."
                )
        content = getattr(response_message, "content", None) or ""
        if "<think>" in content.lower() or "</think>" in content.lower():
            raise RuntimeError(
                f"{self.model} returned thinking tags; "
                "the no-thinking setting was not applied."
            )

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self.history.append(self.messages[-1])

    def add_user_image_message(self, image_urls, text):
        message = {
            "role": "user", 
            "content": [
                {"type": "text", "text": text}, 
            ]
        }
        for image_url in image_urls:
            base64_image = encode_image(image_url)
            message["content"].append({
                "type": "image_url", 
                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
            })
        self.messages.append(message)
        self.history.append(self.messages[-1])

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
        self.history.append(self.messages[-1])

    def get_system_response(self) -> str:
        return "understanding:\n\nAction: turn-right 40"
        try:
            self.do_truncation = False

            response = self.client.chat.completions.create(
                **self._completion_kwargs(self.messages)
            )
            response_message = response.choices[0].message
            self._validate_no_thinking(response_message)

            usage_tokens = response.usage.total_tokens
            self.usage_tokens = usage_tokens
            self.cost += usage_tokens * self.price / 1000
            print(
                f"[ChatGPT] current model {self.model}, usage_tokens: {usage_tokens}, "
                f"cost: ${self.cost:.5f}, price: ${self.price:.5f}"
            )
            if usage_tokens > self.max_limit:
                print(
                    f"[ChatGPT] truncate the conversation to avoid token usage limit, save money"
                )
                self.truncate()
            
            # To avoid failure response, you need to add_assistant message by yourself after you get a correct response
            # self.history.append({
            #         "role": "assistant",
            #         "content": response_message.content
            #     })
            return response_message.content
            # return "No, I am not sure. Move forward 1.575 meter."
        except Exception as e:
            logger.warning(f"[ChatGPT] Error: {e}")
            if self.fail_fast:
                raise
            return "Sorry, I am not able to respond to that."

    def get_system_response_with_content(self, sys_prompt, content) -> str:
        try:
            self.do_truncation = False

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": content},
            ]

            response = self.client.chat.completions.create(
                **self._completion_kwargs(messages)
            )
            
            response_message = response.choices[0].message
            self._validate_no_thinking(response_message)

            usage_tokens = response.usage.total_tokens
            self.usage_tokens = usage_tokens
            self.cost += usage_tokens * self.price / 1000
            print(
                f"[ChatGPT] current model {self.model}, usage_tokens: {usage_tokens}, "
                f"cost: ${self.cost:.5f}, price: ${self.price:.5f}"
            )
            # This method is stateless: every scoring/answering request is
            # rebuilt, and the serving endpoint enforces the 65,536-token cap.
            self.messages = messages
            
            # To avoid failure response, you need to add_assistant message by yourself after you get a correct response
            # self.history.append({
            #         "role": "assistant",
            #         "content": response_message.content
            #     })
            return response_message.content
            # return "No, I am not sure. Move forward 1.575 meter."
        except Exception as e:
            logger.warning(f"[ChatGPT] Error: {e}")
            if self.fail_fast:
                raise
            return "Sorry, I am not able to respond to that."

    def get_system_response_stream(self):
        response = self.client.chat.completions.create(
            **self._completion_kwargs(self.messages, stream=True)
        )
        for chuck in response:
            if len(chuck.choices) > 0 and chuck.choices[0].finish_reason != "stop":
                if chuck.choices[0].delta.content is None:
                    continue
                yield chuck.choices[0].delta.content

        # stream mode does not support token usage check, give a rough estimation
        usage_tokens = int(sum([len(item["content"]) for item in self.message]) / 3.5)
        self.usage_tokens = usage_tokens
        self.cost += usage_tokens * self.price / 1000
        logger.info(
            f"[ChatGPT] current model {self.model}, usage_tokens approximation: {usage_tokens},"
            f" cost: ${self.cost:.2f}, price: ${self.price:.2f}"
        )

        if usage_tokens > self.max_limit:
            logger.info(
                f"[ChatGPT] truncate the conversation to avoid token usage limit"
            )
            self.truncate()

    @property
    def message(self):
        return self.messages

    @message.setter
    def message(self, message):
        """
        Usually at the dialog begining
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message_first_turn},
        {"role": "assistant", "content": assistant_message_first_turn},
        """
        self.init_length = len(message)
        self.messages = message
        self.history.extend(self.messages)

    def truncate(self, percentage: int = 3):
        self.do_truncation = True
        usr_idx = [
            idx
            for idx in range(len(self.messages))
            if self.messages[idx]["role"] == "user"
        ]
        middle_idx = usr_idx[len(usr_idx) // percentage]
        logger.info(
            f"\033[33m [ChatGPT] truncate the conversation at index: {middle_idx} from {usr_idx} \033[m"
        )
        self.messages = self.messages[: self.init_length] + self.messages[middle_idx:]

    def clear(self):
        """end the conversation"""
        self.messages = []
        self.history = []



if __name__ == "__main__":
    config = AzureConfig("gpt-4o")
    chat_api = ChatAPI(config)
    chat_api.message = [
        {"role": "system", "content": "Are you chatGPT?"},
        {"role": "user", "content": "Answer Yes or No."},
    ]
    # print(chat_api.messages)
    # user_input = input("User: ")
    # chat_api.add_user_message(user_input)
    # print(chat_api.messages)
    # print(chat_api.cost)
    print(chat_api.get_system_response_with_content("You are chat assistant.", "Hello!"))
