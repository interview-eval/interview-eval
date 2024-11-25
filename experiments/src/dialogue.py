import json
import os
import time
from abc import ABC, abstractmethod
from random import randint
from typing import Dict, List, Optional, Tuple

import pandas as pd
from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from src.base_agent import BaseAgent, DialogueAgent, EvaluateAgent
from src.base_state import InterviewState, StateMachine
from src.prompt import SESSION_SUMMARIZE_PROMPT
from src.utils import extract_json, select_queries, write_csv_row


class Moderator:
    def __init__(
        self,
        model: ChatOpenAI,
        summarizer: ChatOpenAI,
        system_message,
        queries: dict,
        references: dict,
        store_session: bool,
        agents_name: list,
        followup_flag: int,
        start_query_index: int,
        state_threshold: int,
        state_threshold_followup: int,
        init_action: str,
    ) -> None:

        self.model = model
        self.summarizer = summarizer
        self.system_message = system_message
        self.queries = queries
        self.reference = references
        self.agents_name = agents_name
        num_query = len(self.queries)
        self.global_state_flow = {i: [] for i in range(num_query)}
        self.session_state_flow = []
        self.query_index_flow = []
        self.global_message_history = {i: [] for i in range(num_query)}
        self.global_message_summary_history = {i: [] for i in range(num_query)}
        self.session_history = []
        self.query_history = {i: [] for i in range(num_query)}
        self.session_num = 0
        self.store_session = True if store_session == None else store_session
        self.init_action = init_action
        # self.current_query_index = (
        #     0
        #     if start_query_index == "start"
        #     else len(queries) - 1 if start_query_index == "end" else len(queries) // 2
        # )
        self.current_query_index = start_query_index
        self.state_threshold = state_threshold
        self.state_threshold_followup = state_threshold_followup
        self.followup_flag = followup_flag

    def reset(self) -> None:
        if not self.session_num == 0:
            self.global_state_flow[self.current_query_index].append(self.session_state_flow)
            self.global_message_history[self.current_query_index].append("\n".join(self.session_history))
            if self.store_session:
                self.summarize_session()
        self.state_machine = StateMachine(interview_type=self.task_type)
        self.state_machine.init_action(self.init_action)
        self.session_state_flow = []
        self.session_history = []
        self.session_num += 1

    def send_query(self):
        try:
            flag = 0 if "FAIL" in self.global_state_flow[self.current_query_index][-1][-3] else 1
        except:
            flag = 1
        self.current_query = self._select_queries(flag)

        if self.current_query is None:
            self.action = "query_finished"
            prompt = None
        else:
            self.action = self.state_machine.action
            self._gen_queries(self.current_query)
            prompt = self.state_machine.get_initial_prompt(self.current_query)
        self.session_history.append(f"{self.speaker}: {prompt}")
        self.declare_state()  # INIT -> UNC/EXP
        return prompt

    def _select_queries(self, flag=0):
        # current_query, self.query_history, self.current_query_index = select_queries(
        #     self.queries, self.query_history, self.current_query_index, flag
        # )
        # self.query_index_flow.append(self.current_query_index)
        try:

            try:
                level_idx = self.current_query_index % len(self.queries)
                q_idx = self.current_query_index // len(self.queries)
                current_query = self.queries[level_idx][q_idx]
            except:
                if self.current_query_index == len(self.queries):
                    current_query = None
                q_idx = self.current_query_index  # % len(self.queries)
                current_query = self.queries.iloc[q_idx]
                current_query = current_query.to_dict()
        except:
            current_query = None
        self.current_query_index += 1
        return current_query

    def get_prompt(self):
        return self.state_machine.get_prompt(self.current_query, self.session_history, self.model)

    def _gen_queries(self, current_query) -> dict:
        current_query["initial_question"] = current_query["initial_question"].replace("²", "^2")
        if self.action != "None":
            try:
                query_generation_prompt = self.get_prompt()
                new_prob = self.model.invoke(
                    [
                        HumanMessage(content=f"""{query_generation_prompt}"""),
                    ]
                )
                new_prob = extract_json(new_prob.content)

                current_query["explanation"] = ""
                current_query["deleted_information"] = ""
                if self.action == "unclarifying":
                    try:
                        current_query["deleted_information"] = new_prob["deleted_information"]
                        current_query["explanation"] = new_prob["explanation"]
                        if current_query["deleted_information"].lower() == "none":
                            self.action = "None"
                            current_query["revised_question"] = current_query["inital_question"]
                        else:
                            current_query["revised_question"] = new_prob["revised_question"]
                    except:
                        current_query["deleted_information"] = "None"
                        current_query["revised_question"] = current_query["initial_question"]
                        self.action = "None"
                elif self.action == "adding":

                    try:
                        try:
                            current_query["revised_question"] = new_prob["paraphrased_merged_question"]
                        except:
                            current_query["revised_question"] = new_prob["merged_question"]
                    except:
                        self.action = "None"
                        current_query["revised_question"] = current_query["initial_question"]
                elif self.action == "modifying":
                    try:
                        try:
                            current_query["revised_question"] = new_prob["new_question"]
                            current_query["revised_solution"] = new_prob["new_solution"]
                        except:
                            current_query["revised_question"] = new_prob["new_question"]
                    except:
                        self.action = "None"
                        current_query["revised_question"] = current_query["initial_question"]

                elif self.action == "paraphrasing":
                    try:
                        current_query["revised_question"] = new_prob["revised_question"]
                    except:
                        self.action = "None"
                        current_query["revised_question"] = current_query["initial_question"]
            except:
                self.action = "None"
                current_query["revised_question"] = current_query["initial_question"]

        elif self.action == "None":
            current_query["revised_question"] = current_query["initial_question"]

        return current_query

    def receive_and_send(self, speaker: str, message: str) -> tuple[str, str]:
        if speaker == self.agents_name[0]:  # evaluatee
            self.session_history.append(f"{speaker}: {message}")
            message = self.get_prompt()
            next_speaker = self.agents_name[1]
        elif speaker == self.agents_name[1]:  # evaluator
            message, self.action = self.state_machine.extract_message(solution=self.current_query, message=message)
            self.session_history.append(f"{speaker}: {message}")
            self.declare_state()
            if self.state_machine.state.name not in [
                "SOLVE_SUCCESS",
                "SOLVE_FAIL",
                "QUESTION_COMPLETE",
                "EVALUATION_COMPLETE",
                "MOVING_TO_NEXT_QUESTION",
            ]:
                next_speaker = self.agents_name[0]
            else:
                next_speaker = self.agents_name[1]
        return next_speaker, message, self.state_machine.state

    def declare_state(self):
        self.prev_state = self.state_machine.state
        self.state = self.state_machine.transition(
            self.action, self.state_threshold, self.state_threshold_followup, self.followup_flag
        )
        self.session_state_flow.append(self.state.name)

        print(f"\n**STATE TRANSITION**\nSTATE {self.prev_state.name} -> STATE {self.state.name}\n")

    def summarize_session(self) -> None:
        summary = self._summarize(self.session_history)
        self.global_message_summary_history[self.current_query_index // 3].append(summary)

    def _summarize(self, session_history):

        prompt = SESSION_SUMMARIZE_PROMPT.format(
            system_name=self.agents_name[0], user_name=self.agents_name[1], session_history=session_history
        )
        message = self.summarizer.invoke(prompt)
        return message.content


class DialogueSimulator:
    def __init__(self, agents: dict[DialogueAgent], moderator, selection_function, task_type, output_path) -> None:
        self.agents = agents
        self.moderator = moderator
        self.moderator.task_type = task_type
        self._step = 0
        self.message_history = []
        self.session_history = []
        self.select_next_speaker = selection_function
        self.output_path = output_path
        self.start_time = time.time()

    def reset(self):
        for name in self.agents.keys():
            self.agents[name].reset()
        # send initial queries
        self.moderator.reset()
        self.moderator.agents_name = list(self.agents.keys())
        self.moderator.speaker = list(self.agents.keys())[1]
        message = self.moderator.send_query()
        self.session_history.append(f"{self.moderator.speaker}: {message}")
        for receiver in list(self.agents.keys()):
            self.agents[receiver].receive(self.moderator.speaker, message)
        self.next_speaker = list(self.agents.keys())[0]

    def history_reset(self):
        self.message_history = ["Here is the conversation so far."]
        self.session_history = []

    def inject(self, name: str, message: str):
        for agent in self.agents.keys():
            self.agents[agent].receive(name, message)
        self._step += 1

    def step(self) -> tuple[str, str]:
        self.speaker = self.next_speaker
        speaker = self.agents[self.speaker]
        if self.moderator.state_machine.state.name not in [
            "QUESTION_COMPLETE",
            "EVALUATION_COMPLETE",
            "MOVING_TO_NEXT_QUESTION",
        ]:
            agent_message = speaker.send()
        else:
            agent_message = ""
        self.next_speaker, message, state = self.moderator.receive_and_send(self.speaker, agent_message)
        if self.speaker == self.next_speaker:
            self.inject(self.speaker, message)
            message = self.moderator.get_prompt()
            self.agents[self.next_speaker].receive(self.speaker, message)
        else:
            self.agents[self.next_speaker].receive(self.speaker, message)
            self._step += 1
        if state.name == "SESSION_START":
            self.save_attributes_to_file(self.output_path)
            self.reset()

        return self.speaker, agent_message

    def save_attributes_to_file(self, output_path):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time  # Calculate duration
        # Convert the dictionary to a DataFrame
        head = [
            "idx",
            "solution",
            "session_history",
            "state_flow",
            "correctness_main",
            "correctness_sub_main",
            "correctness_main_detail",
            "correctness_followup",
            "error_type",
            "feedback_types",
            "followup_types",
            "cost_grader",
            "cost_interviewer",
            "cost_interviewee",
            "duration",
        ]
        value = [
            self.moderator.current_query_index,
            self.moderator.current_query,
            self.moderator.session_history,
            self.moderator.session_state_flow,
            self.moderator.state_machine.success,
            self.moderator.state_machine.recall,
            self.moderator.state_machine.TF,
            self.moderator.state_machine.success_followup,
            self.moderator.state_machine.error_types,
            self.moderator.state_machine.feedback_types,
            self.moderator.state_machine.follow_up_types,
            self.moderator.state_machine.cost_grader,
            self.agents[self.moderator.agents_name[1]].cost,
            self.agents[self.moderator.agents_name[0]].cost,
            self.duration,
        ]
        if not os.path.exists(output_path):
            write_csv_row(head, output_path)
        write_csv_row(value, output_path)


def select_next_speaker(step: int, agents: List[DialogueAgent]) -> int:
    return step % len(agents)
