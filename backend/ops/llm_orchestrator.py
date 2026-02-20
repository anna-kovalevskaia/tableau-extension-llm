import json
from backend.models import LLMResponseModel

required_keys = ["required_fields", "code"]

class LLMPlannerError(Exception):
    pass

class LLMPlanner:
    def __init__(self,system_prompt_planner,user_id, history,llm):
        self.system_prompt_planner = system_prompt_planner
        self.user_id = user_id
        self.history = history
        self.llm = llm


    def _get_last_role_content(self, role, msg_history):
        try:
            return next(
                    message["content"]
                    for message in reversed(msg_history)
                    if message["role"] == role
                )
        except StopIteration:
            raise LLMPlannerError(f"{self.user_id} doesn't have history for required role : {role}")


    def get_llm_plan(self, datetime):
        """get_llm_plan
        Sends question + available_fields to LLM and returns raw JSON response from the model.
        updates history
        """
        msg_history = self.history.get_history(self.user_id)
        user_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in msg_history
            if msg["role"] not in ("planner_input", "chunking_input", "interpreter_input")
        ]

        messages = [
            {"role": "system", "content": self.system_prompt_planner},
            *user_history,
            {
                "role": "user",
                "content": json.dumps(
                    self._get_last_role_content("planner_input", msg_history),
                    ensure_ascii=False
                )
            }
        ]

        raw_response = self.llm(messages)
        self.history.add_message(self.user_id, "assistant", raw_response, datetime)

        return raw_response


    def parse_llm_plan(self, raw_response):
        """
        Parses raw LLM JSON response and returns a validated Pydantic model
        (LLMResponseModelByIndex or LLMResponseModelByDate).
        Raises LLMPlannerError if structure is invalid.
        """

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            raise LLMPlannerError(f"LLM returned invalid JSON:\n{raw_response}")

        try:
            return LLMResponseModel(**parsed)
        except Exception as e:
            raise LLMPlannerError(f"LLM responded invalid structure or filter-filed: {e}")


class LLMInterpreter:
    def __init__(self, system_prompt_interpreter, user_id, history, llm):
        self.system_prompt_interpreter = system_prompt_interpreter
        self.user_id = user_id
        self.history = history
        self.llm = llm

    def llm_interpretation(self, execution_result):

        messages = [
            {"role": "system", "content": self.system_prompt_interpreter},
            *self.history.get_history(self.user_id),
            {
                "role": "user",
                "content": json.dumps({
                    "result_for_execution": execution_result
                }, ensure_ascii=False)
            }
        ]

        self.history.add_message(self.user_id, "user", "Explain the result")
        raw_response = self.llm.ask(messages)
        self.history.add_message(self.user_id, "assistant", raw_response)

        return raw_response
