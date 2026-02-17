import json
from typing import List
from pydantic import BaseModel
from backend.utilities.logging_config import setup_logging

logger = setup_logging(filename='llm_planner_error.log')
required_keys = ["required_fields", "code"]

class LLMPlannerError(Exception):
    pass

class LLMResponseModel(BaseModel):

    required_fields: List[str]
    code: str

class LLMPlanner:
    def __init__(self,system_prompt_planner,user_id,question,history,llm):
        self.system_prompt_planner = system_prompt_planner
        self.user_id = user_id
        self.question = question
        self.history = history
        self.llm = llm


    def get_llm_plan(self, sheet_name, fields):
        """get_llm_plan
        Sends question + available_fields to LLM, updates history,
        and returns raw JSON response from the model.
        """

        messages = [
            {"role": "system", "content": self.system_prompt_planner},
            *self.history.get_history(self.user_id),
            {
                "role": "user",
                "content": json.dumps({
                    "question": self.question,
                    "sheets": {'sheet': sheet_name, "available_fields": fields},
                }, ensure_ascii=False)
            }
        ]

        self.history.add_message(self.user_id, "user",self.question)
        raw_response = self.llm.ask(messages)
        self.history.add_message(self.user_id, "assistant", raw_response)

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
            logger.error(f"JSON parsing error:\n{raw_response}")
            raise LLMPlannerError(f"LLM returned invalid JSON:\n{raw_response}")

        try:
            return LLMResponseModel(**parsed)
        except Exception as e:
            logger.error(f"Data structure error: {e}\n {parsed}")
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
