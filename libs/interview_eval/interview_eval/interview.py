import json
import logging
import pandas as pd
# import dataclass
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from interview_eval.swarm import Agent, Result, Swarm
from interview_eval.utils import get_json_prompt


@dataclass
class Response:
    messages: list
    agent: Agent
    context_variables: dict


class Interviewer(Agent):
    def __init__(
        self,
        config: dict,
        name: Optional[str] = None,
    ):
        interviewer_config = config["interviewer"]
        name = name or interviewer_config["name"]
        client_kwargs = interviewer_config.get("client", None)
        client = OpenAI(**client_kwargs) if client_kwargs else OpenAI()

        instructions = (
            interviewer_config["instructions"]
            + f"\nRubric:\n{interviewer_config['rubric']}\n"
        )
        strategy = f"\nStrategy:\n{yaml.dump(interviewer_config['strategy'], default_flow_style=False)}"
        super().__init__(
            name=name,
            instructions=instructions,
            functions=[self.conclude_interview],
            client=client,
        )
        self.strategy = strategy
        self.seed_question = interviewer_config.get("seed_question", "")
        self.seed_question_answer = interviewer_config.get("seed_question_answer", "")
        self.interviewer_config = interviewer_config

    def conclude_interview(self, score: int, comments: str) -> Result:
        """End interview with final assessment.

        Called when max questions reached, understanding established, or unable to progress further.
        Also called when forced to conclude interview.

        Args:
            score (int): Final score (0-10) based on rubric
            comments (str): Overall evaluation including strengths,
                weaknesses, and areas for improvement

        Returns:
            Result: Final assessment with score and detailed feedback
        """
        return Result(
            value=f"Interview concluded. Score: {score}/10\nComments: {comments}",
            context_variables={
                "interview_complete": True,
                "score": score,
                "comments": comments,
            },
        )


class Interviewee(Agent):
    def __init__(
        self,
        config: dict,
        name: Optional[str] = None,
    ):

        interviewee_config = config["interviewee"]
        name = name or interviewee_config["name"]
        client_kwargs = interviewee_config.get("client", None)
        client = OpenAI(**client_kwargs) if client_kwargs else OpenAI()

        instructions = interviewee_config["instructions"]
        super().__init__(name=name, instructions=instructions, client=client)

class InterviewReportManager:
    def __init__(self):
        # Initialize the DataFrame with the desired structure
        self.interview_data = pd.DataFrame(columns=["interview_id", "question"])
        self.current_interview_id = None

    def start_new_interview(self):
        # Determine the next interview_id
        if not self.interview_data.empty:
            self.current_interview_id = self.interview_data["interview_id"].max() + 1
        else:
            self.current_interview_id = 1

    def log_attempt(self, question: str, retrial: int, is_correct: bool):
        # Check if the question already exists in the DataFrame
        if question not in self.interview_data["question"].values:
            # Add a new row for the question
            new_row = {"interview_id": self.current_interview_id, "question": question}
            self.interview_data = pd.concat([self.interview_data, pd.DataFrame([new_row])], ignore_index=True)

        # Ensure the retrial column exists, create it dynamically if needed
        column_name = f"retrial_{retrial}"
        if column_name not in self.interview_data.columns:
            self.interview_data[column_name] = None

        # Update the appropriate retrial column
        self.interview_data.loc[
            (self.interview_data["question"] == question) &
            (self.interview_data["interview_id"] == self.current_interview_id),
            column_name
        ] = is_correct

    def get_interview_data(self):
        # Return the logged data for analysis or export
        return self.interview_data

    def save_to_csv(self, filename: str):
        # Save the DataFrame to a CSV file
        self.interview_data.to_csv(filename, index=False)

    def load_from_csv(self, filename: str):
        # Load the DataFrame from a CSV file
        self.interview_data = pd.read_csv(filename)

class InterviewRunner:
    def __init__(
        self,
        interviewer: Agent,
        interviewee: Agent,
        config: dict,
        logger: logging.Logger,
        console: Console,
        report_manager: InterviewReportManager
    ):
        self.client = Swarm()
        self.interviewer = interviewer
        self.interviewee = interviewee
        self.config = config
        self.logger = logger
        self.console = console
        self.questions_count = 0
        self.max_questions = config["session"].get("max_questions", 10)  # Default to 10 questions if not specified
        self.max_retries = config["session"].get("max_retries", 3)  # Default to 3 retries if not specified
        self.hint_prompt_template = config["interviewer"].get("hint_prompt_template","Given the following, you have to give a hint to the interviewee to help them answer the question correctly. \nIf the {interviewee_name} makes repeated mistakes, give more hints to fix the mistake.\n") 
        self.interviewer_messages = []
        self.interviewee_messages = []
        self.feedbacks = []
        self.questions = []
        self.seed_question_used = False
        self.report_manager = report_manager
    def display_message(self, agent_name: str, content: str):
        """Display a message with proper formatting."""

        agent_name_to_style = {
            self.interviewer.name.lower(): "interviewer",
            self.interviewee.name.lower(): "interviewee",
            "feedback agent": "feedback agent",
        }

        style = agent_name_to_style[agent_name.lower()]
        panel = Panel(
            content,
            title=f"[{style}]{agent_name}[/{style}]",
            border_style=style,
            padding=(1, 2),
        )
        # Only print to console if in verbose mode
        if self.logger.getEffectiveLevel() <= logging.INFO:
            self.console.print(panel)

        # Always log to file if file logging is enabled
        self.logger.info(f"{agent_name}: {content}")

    def display_results(self, results: Dict[str, Any]):
        """Display interview results with formatting."""
        score = results["score"]
        score_color = "success" if score >= 7 else "warning" if score >= 5 else "error"

        results_panel = Panel(
            f"\n[{score_color}]Final Score: {score}/10[/{score_color}]\n\n"
            f"[info]Questions Asked: {results['questions_asked']}[/info]\n\n"
            f"[white]Feedback:[/white]\n{results['feedback']}",
            title="[success]Interview Assessment Results[/success]",
            border_style="success",
            padding=(1, 2),
        )
        self.console.print("\n")
        self.console.print(results_panel)

    def _get_response(self, agent: Agent, messages: list, context: dict) -> Result:
        """Helper method to get response with progress spinner."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing response...", total=None)
            return self.client.run(agent=agent, messages=messages, context_variables=context)

    def _get_response_raw(self, agent: Agent, messages: list, chat_params: dict, json: bool = False) -> Response:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing response...", total=None)
            full_params = {
                "model": agent.model,
                "messages": messages,
            }

            if json:
                full_params["response_format"] = {"type": "json_object"}

            full_params.update(chat_params)
            raw_response = agent.client.chat.completions.create(**full_params)
            content = raw_response.choices[0].message.content
            return Response(messages=[{"role": "assistant", "content": content}], agent=agent, context_variables={})

    def add_message(self, speaker, content):
        """Add messages to both conversation tracks based on who's speaking.

        When interviewer speaks: they're the assistant, interviewee is the user
        When interviewee speaks: they're the assistant, interviewer is the user
        """
        if speaker == self.interviewer:
            # Interviewer is speaking (as assistant) to interviewee (as user)
            self.interviewer_messages.extend([{"role": "assistant", "content": content}])
            self.interviewee_messages.extend([{"role": "user", "content": content}])
        else:
            # Interviewee is speaking (as assistant) to interviewer (as user)
            self.interviewer_messages.extend([{"role": "user", "content": content}])
            self.interviewee_messages.extend([{"role": "assistant", "content": content}])

    def call_feedback_agent(self, question, response):
        if question == self.interviewer.seed_question and self.interviewer.seed_question_answer is not None:
            
            last_msg_content = "Question: " + question + "\nReference Answer: " + self.interviewer.seed_question_answer +  "\nResponse: " + response
        else:
            last_msg_content = "Question: " + question + "\nResponse: " + response
            
        
        conditional_ref_prompt = "" if self.interviewer.seed_question_answer is None else f" and reference answer to the question"

        json_prompt = get_json_prompt(
            {
                "feedback": "langauge critique string",
                "correctness": "boolean indicating the correctness of the response",
            }
        )
        full_prompt = (
            f"Given a grading rubric, provide a concise language critique in 2 sentences evaluating the response based the previous question{conditional_ref_prompt}, along with a boolean value indicating the correctness of the response.\n\n### Score Rubric:\n{self.interviewer.interviewer_config['rubric']}\n\n### Response:\n{last_msg_content}\n"
            + json_prompt
        )
        fmsg = [{"role": "user", "content": full_prompt}]

        temp_msg = self._get_response_raw(self.interviewer, fmsg, {}, json=True)
        response_dict = json.loads(temp_msg.messages[-1]["content"])
        feedback = response_dict["feedback"]
        is_correct = response_dict["correctness"]

        assert isinstance(feedback, str), "Generation Error in Feedback Agent: Feedback should be a string"
        assert is_correct in [
            True,
            False,
        ], "Generation Error in Feedback Agent: `is_correct` should be a boolean value"
        return feedback, is_correct

    def call_hint_agent(self, question, response, feedback):

        chat_history_str = "### Previous Chat History\n\n"
        for message in self.interviewee_messages:
            if message["role"] == "assistant":
                chat_history_str += f"{self.interviewee.name}: {message['content']}\n"
            else:
                chat_history_str += f"You: {message['content']}\n"

        chat_history_str += "\n"

        last_msg_content = chat_history_str + "Question: " + question + "\nResponse: " + response + "\nFeedback: " + feedback

        hint_msg = [
            {
                "role": "user",
                "content": self.hint_prompt_template.format(
                    interviewee_name=self.interviewee.name)+last_msg_content
                ,
            }
        ]

        response = self._get_response_raw(self.interviewer, hint_msg, {})
        return response.messages[-1]["content"]

    def call_question_agent(self, question, response):

        chat_history_str = "### Previous Chat History\n\n"
        for message in self.interviewer_messages:
            if message["role"] == "user":
                chat_history_str += f"{self.interviewee.name}: {message['content']}\n"
            else:
                chat_history_str += f"You: {message['content']}\n"

        chat_history_str += "\n"
        if self.interviewer.seed_question_answer is not None:
            last_msg_content = chat_history_str + "\nReference Solution" + self.interviewer.seed_question_answer
        else:
            last_msg_content = chat_history_str
        import pdb;pdb.set_trace()
        followup_prompt = (
            "Given the following, you have to generate a followup question based on the following instruction, and the previous log. Also, refer to the reference solution of the original question. " 
            + f"Questioning instruction: {self.interviewer.strategy}\nPrevious Log: {last_msg_content}"
        )

        question_msg = [
            {
                "role": "user",
                "content": followup_prompt,
            }
        ]
        import pdb;pdb.set_trace()
        response = self._get_response(self.interviewer, question_msg, {})
        return response.messages[-1]["content"]

    # Note: Please follow the convention of adding the message to the conversation first and then displaying it
    def run(self) -> Dict[str, Any]:
        """Run the interview and return results."""
        self.console.print("\n[info]Starting Interview Session...[/info]\n")

        initial_message = self.config["session"]["initial_message"]
        self.add_message(self.interviewer, initial_message)
        self.display_message(self.interviewer.name, initial_message)

        context = self.config["session"]["initial_context"]
        response = self._get_response(self.interviewee, self.interviewee_messages, context)
        self.add_message(self.interviewee, response.messages[-1]["content"])
        self.display_message(response.agent.name, response.messages[-1]["content"])

        # Start the interview loop
        self.questions_count += 1
        self.console.print(f"\n[info]Question {self.questions_count}[/info]")

        if (
            not self.seed_question_used
            and hasattr(self.interviewer, "seed_question")
            and self.interviewer.seed_question
        ):
            # Use the seed question for the first question
            interviewer_response = Response(
                messages=[{"role": "assistant", "content": self.interviewer.seed_question}],
                agent=self.interviewer,
                context_variables={},
            )
            self.seed_question_used = True
            self.questions.append(self.interviewer.seed_question)
        else:
            # Generate a question as usual
            interviewer_response = self._get_response(self.interviewer, self.interviewer_messages, {})

        response = interviewer_response
        self.add_message(self.interviewer, response.messages[-1]["content"])
        self.display_message(self.interviewer.name, response.messages[-1]["content"])
        
        while self.questions_count <= self.max_questions:
            # 1. Get response from interviewee
            question = self.interviewer_messages[-1]["content"]
            response = self._get_response(self.interviewee, self.interviewee_messages, {}).messages[-1]["content"]
            self.add_message(self.interviewee, response)
            self.display_message(self.interviewee.name, response)

            # 2. Get feedback from feedback agent. Note that the message from feedback agent is not added to the conversation
            feedback, is_correct = self.call_feedback_agent(question, response)
            self.report_manager.log_attempt(question, 0, is_correct)
            self.feedbacks.append(feedback)
            self.display_message(
                "Feedback Agent",
                feedback + ("\n\nCorrectness: True" if is_correct else "\n\nCorrectness: False"),
            )

            # Retry the question `self.max_retries`` times if the response is incorrect
            if not is_correct:
                # Retry the question, if max retries not reached
                # Check if cur_retry is initialized and increment it
                current_retry = 0

                while current_retry < self.max_retries and is_correct == False:
                    self.console.print(
                        f"\n[info]Retrying Question {self.questions_count}, Current number of retrials: {current_retry}"
                    )

                    hint = self.call_hint_agent(question, response, feedback)
                    self.add_message(self.interviewer, hint)
                    self.display_message(self.interviewer.name, hint)

                    response = self._get_response(self.interviewee, self.interviewee_messages, {}).messages[-1][
                        "content"
                    ]
                    self.add_message(self.interviewee, response)
                    self.display_message(self.interviewee.name, response)

                    feedback, is_correct = self.call_feedback_agent(question, response)
                    self.report_manager.log_attempt(question, current_retry+1, is_correct)
                    self.feedbacks.append(feedback)
                    self.display_message(
                        "Feedback Agent",
                        feedback + ("\n\nCorrectness: True" if is_correct else "\n\nCorrectness: False"),
                    )
                    current_retry += 1
                if is_correct == False:
                    # If max retries reached, get next question
                    self.current_retry = None
                    move_on_after_fails = (
                        "I think this question is too difficult for you. Let's move on to the next question."
                    )
                    self.add_message(self.interviewer, move_on_after_fails)
                    self.display_message(self.interviewer.name, move_on_after_fails)

            # Reset the interviewee messages when moving on to the next question
            self.interviewee_messages = []

            self.questions_count += 1
            if self.questions_count <= self.max_questions:
                self.console.print(f"\n[info]Question {self.questions_count}")
                response = self.call_question_agent(self.interviewer, self.interviewer_messages)
                self.questions.append(response)
                self.add_message(self.interviewer, response)
                self.display_message(self.interviewer.name, response)

            # 4. Check end conditions for the interview
            if self.questions_count > self.max_questions:
                final_message = "Maximum number of questions reached. Concluding interview."
                self.console.print(f"\n[warning]{final_message}[/warning]")
                self.interviewer_messages.append({"role": "assistant", "content": final_message})
                response = self._get_response(self.interviewer, self.interviewer_messages, {"force_conclude": True})
                self.display_message(response.agent.name, response.messages[-1]["content"])
                break

        results = {
            "score": response.context_variables["score"],
            "feedback": response.context_variables["comments"],
            "questions_asked": self.questions_count - 1,
        }

        self.display_results(results)
        return results

