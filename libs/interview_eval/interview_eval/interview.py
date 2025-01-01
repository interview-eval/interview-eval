import json
import logging
import pandas as pd
import random
import os
import re
from datetime import datetime
from pathlib import Path

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
        self.seed_question = interviewer_config.get("seed_question", None)
        self.seed_question_answer = interviewer_config.get(
            "seed_question_answer", None)
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
    def __init__(self, config):
        # Initialize DataFrames for attempts and summaries
        self.interview_data = pd.DataFrame(
            columns=["interview_id", "question"])
        self.summaries_data = pd.DataFrame(
            columns=[
                "interview_id",
                "review",
                "score",
                "questions_asked",
                "log_file_path"])
        self.current_interview_id = None
        self.config = config

    def start_interview(self, log_file_path):
        # Determine the next interview_id
        if not self.interview_data.empty:
            self.current_interview_id = self.interview_data["interview_id"].max(
            ) + 1
        else:
            self.current_interview_id = 1
        self.log_file_path = log_file_path
        # Add an entry for the summary DataFrame
        new_summary_row = {"interview_id": self.current_interview_id}
        self.summaries_data = pd.concat(
            [self.summaries_data, pd.DataFrame([new_summary_row])], ignore_index=True)

    def log_attempt(self, question: str, retrial: int, is_correct: bool):
        # Check if the question already exists in the DataFrame
        if not ((self.interview_data["question"] == question) &
                (self.interview_data["interview_id"] == self.current_interview_id)).any():
            # Add a new row for the question
            new_row = {
                "interview_id": self.current_interview_id,
                "question": question}
            self.interview_data = pd.concat(
                [self.interview_data, pd.DataFrame([new_row])], ignore_index=True)

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

    def complete_interview(self, results: dict):
        if self.current_interview_id not in self.summaries_data["interview_id"].values:
            raise ValueError(
                f"Interview ID {self.current_interview_id} does not exist in summaries.")
        self.summaries_data.loc[
            self.summaries_data["interview_id"] == self.current_interview_id,
            ["review", "score", "questions_asked", "log_file_path"]
        ] = [results["feedback"], results["score"], results["questions_asked"], self.log_file_path]

    def group_by_score(self):
        """
        Group log file paths by score from the summary database, keeping only score and log_file_path.

        Returns:
            dict: A dictionary where the keys are scores, and the values are lists of log file paths.
        """
        if not hasattr(self, "summaries_data") or self.summaries_data.empty:
            return {}

        # Ensure only 'score' and 'log_file_path' columns remain
        temp_db = self.summaries_data[["score", "log_file_path"]]

        # Group by score and aggregate log_file_path into lists
        grouped = (
            temp_db.groupby("score")["log_file_path"]
            .apply(list)
            .to_dict()
        )
        return grouped

    def calculate_final_scores(self):
        """Calculate averages for head rows and remaining rows, filling missing retrial values row-by-row."""
        # Dynamically identify retrial columns
        retrial_columns = [
            col for col in self.interview_data.columns if col.startswith("retrial_")]

        # Fill missing retrial values row-by-row
        def fill_row(row):
            if not row.isna().any():
                return row
            for i in range(1, len(retrial_columns)):
                current_col = retrial_columns[i]
                previous_col = retrial_columns[i - 1]
                if pd.isna(row[current_col]
                           ):  # Check if current column value is NaN
                    # Fill with previous column's value
                    row[current_col] = row[previous_col]
            return row

        # Apply the fill logic to all rows
        filled_data = self.interview_data.apply(fill_row, axis=1)

        # Group data into head rows and remaining rows
        head_rows = filled_data.groupby("interview_id").head(
            1)  # First row of each interview
        remaining_rows = filled_data.groupby(
            "interview_id").apply(lambda group: group.iloc[1:])

        # Calculate averages for head rows
        head_averages = {col: head_rows[col].mean() for col in retrial_columns}

        # Calculate averages for remaining rows
        remaining_averages = {
            col: remaining_rows[col].mean() for col in retrial_columns}

        return {
            "seed_question_scores": head_averages,
            "followup_question_scores": remaining_averages,
        }

    def generate_final_summary(self, agent):
        """
        Generate a final summary of strengths and weaknesses based on scores.
        Weaknesses are derived from the lowest 30% of scores, and strengths from the highest 30%.
        Summarize each group separately, then combine into a final summary.
        """
        # Ensure 'review' and 'score' columns are available
        if "review" not in self.summaries_data.columns or "score" not in self.summaries_data.columns:
            raise ValueError(
                "The summaries_data DataFrame must contain 'review' and 'score' columns.")

        # Drop rows with missing scores or reviews
        valid_data = self.summaries_data.dropna(subset=["review", "score"])

        # Calculate thresholds for bottom 30% and top 30%
        scores = valid_data["score"].sort_values()
        threshold_low = scores.quantile(0.3)
        threshold_high = scores.quantile(0.7)

        # Separate weaknesses and strengths
        weakness_data = valid_data[valid_data["score"] <= threshold_low]
        strength_data = valid_data[valid_data["score"] >= threshold_high]

        # Randomly sample up to 10 reviews from each group
        weaknesses = weakness_data["review"].sample(
            min(10, len(weakness_data)), random_state=42).tolist()
        strengths = strength_data["review"].sample(
            min(10, len(strength_data)), random_state=42).tolist()

        # Summarize weaknesses
        weakness_summary = '\n'.join(weaknesses)
        prompt = f"Summarize the following focusing on the model's weaknesses:\n\n{weakness_summary}"
        full_params = {
            "model": agent.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        raw_response = agent.client.chat.completions.create(**full_params)
        weakness_final_summary = raw_response.choices[0].message.content

        # Summarize strengths
        strength_summary = '\n'.join(strengths)
        if strengths:
            prompt = f"Summarize the following, focusing on the model's strengths.:\n\n{strength_summary}"
            full_params = {
                "model": agent.model,
                "messages": [{"role": "user", "content": prompt}],
            }
            raw_response = agent.client.chat.completions.create(**full_params)
            strength_final_summary = raw_response.choices[0].message.content

        # Combine summaries into the final summary
        final_prompt = (
            f"Combine the following strengths and weaknesses summaries into a final summary:\n\n"
            f"Strengths:\n{strength_final_summary}\n\nWeaknesses:\n{weakness_final_summary}"
        )
        full_params = {
            "model": agent.model,
            "messages": [{"role": "user", "content": final_prompt}],
        }
        raw_response = agent.client.chat.completions.create(**full_params)
        final_summary = raw_response.choices[0].message.content

        return final_summary

    def generate_report(self, agent):
        """
        Combine seed question data, follow-up question data, grouped paths, and summary into a report.
        Save the report to a text file for readability.

        Args:
            agent (Agent): The agent used for generating summaries.
            file_path (str): Path to save the generated report as a .txt file.

        Returns:
            str: A formatted string of the report.
        """
        # Get the required data
        final_scores = self.calculate_final_scores()
        grouped_paths = self.group_by_score()
        summary = self.generate_final_summary(agent)
        # Build the report
        report_lines = [
            "########################################",
            "          INTERVIEW PERFORMANCE REPORT  ",
            "########################################",
            "\n"
        ]

        # Seed Question Scores
        report_lines.append("==> Seed Question Scores <==")
        for retrial, score in final_scores["seed_question_scores"].items():
            report_lines.append(f"  - {retrial}: {score:.2f}")
        report_lines.append("\n")

        # Follow-Up Question Scores
        report_lines.append("==> Follow-Up Question Scores <==")
        for retrial, score in final_scores["followup_question_scores"].items():
            report_lines.append(f"  - {retrial}: {score:.2f}")
        report_lines.append("\n")

        # Grouped Log File Paths
        report_lines.append("==> Log Files Grouped by Score <==")
        for score, paths in grouped_paths.items():
            report_lines.append(f"Score {score}:")
            for path in paths:
                report_lines.append(f"  - {path}")
        report_lines.append("\n")

        # Summary
        report_lines.append("==> Summary <==")
        report_lines.append(summary)
        report_lines.append("\n########################################")

        # Combine lines into a single string
        report_content = "\n".join(report_lines)

        # Save to a text file
        if self.config["report"]["save_to_file"]:
            output_dir = Path(self.config["report"]["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.config["report"]["filename_template"].format(
                timestamp=timestamp)
            filepath = f"{output_dir}/{filename}"
            with open(filepath, "w") as file:
                file.write(report_content)
            print(f"Report successfully saved to {filepath}")
        else:
            print(report_content)
        return report_content

    def get_attempts(self):
        """Retrieve the attempts DataFrame."""
        return self.interview_data

    def get_summaries(self):
        """Retrieve the summaries DataFrame."""
        return self.summaries_data

    def save_to_csv(self, attempts_file="attempts.csv",
                    summaries_file="summaries.csv"):
        """Save both DataFrames to separate CSV files."""
        self.interview_data.to_csv(attempts_file, index=False)
        self.summaries_data.to_csv(summaries_file, index=False)

    def load_from_csv(self, attempts_file="attempts.csv",
                      summaries_file="summaries.csv"):
        """Load both DataFrames from separate CSV files."""
        self.interview_data = pd.read_csv(attempts_file)
        self.summaries_data = pd.read_csv(summaries_file)


class InterviewRunner:
    def __init__(
        self,
        interviewer: Agent,
        interviewee: Agent,
        config: dict,
        logger: logging.Logger,
        log_file_path: str,
        console: Console,
        report_manager: InterviewReportManager
    ):
        self.client = Swarm()
        self.interviewer = interviewer
        self.interviewee = interviewee
        self.config = config
        self.logger = logger
        self.log_file_path = log_file_path
        self.console = console
        self.questions_count = 0
        self.max_questions = config["session"].get(
            "max_questions", 10)  # Default to 10 questions if not specified
        self.max_retries = config["session"].get(
            "max_retries", 3)  # Default to 3 retries if not specified
        self.hint_prompt_template = config["interviewer"].get(
            "hint_prompt_template",
            "Given the following, you have to give a hint to the interviewee to help them answer the question correctly. \nIf the {interviewee_name} makes repeated mistakes, give more hints to fix the mistake.\n")
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

    def _get_response(self, agent: Agent, messages: list,
                      context: dict) -> Result:
        """Helper method to get response with progress spinner."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Processing response...", total=None)
            return self.client.run(
                agent=agent, messages=messages, context_variables=context)

    def _get_response_raw(self, agent: Agent, messages: list,
                          chat_params: dict, json: bool = False) -> Response:
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
            return Response(messages=[
                            {"role": "assistant", "content": content}], agent=agent, context_variables={})

    def add_message(self, speaker, content):
        """Add messages to both conversation tracks based on who's speaking.

        When interviewer speaks: they're the assistant, interviewee is the user
        When interviewee speaks: they're the assistant, interviewer is the user
        """
        if speaker == self.interviewer:
            # Interviewer is speaking (as assistant) to interviewee (as user)
            self.interviewer_messages.extend(
                [{"role": "assistant", "content": content}])
            self.interviewee_messages.extend(
                [{"role": "user", "content": content}])
        else:
            # Interviewee is speaking (as assistant) to interviewer (as user)
            self.interviewer_messages.extend(
                [{"role": "user", "content": content}])
            self.interviewee_messages.extend(
                [{"role": "assistant", "content": content}])

    def call_feedback_agent(self, question, response):
        if question == self.interviewer.seed_question and self.interviewer.seed_question_answer is not None:

            last_msg_content = "Question: " + question + "\nReference Answer: " + \
                self.interviewer.seed_question_answer + "\nResponse: " + response
        else:
            last_msg_content = "Question: " + question + "\nResponse: " + response

        conditional_ref_prompt = "" if self.interviewer.seed_question_answer is None else f" and reference answer to the question"

        json_prompt = get_json_prompt(
            {
                "feedback": "langauge critique string",
                "correctness": "boolean indicating the correctness of the response",
                "score": "score based on the rubric",
            }
        )
        full_prompt = (
            f"Given a grading rubric, provide a concise language critique in 2 sentences evaluating the response based the previous question{conditional_ref_prompt}, along with a boolean value indicating the correctness of the response.\n\n### Score Rubric:\n{self.interviewer.interviewer_config['rubric']}\n\n### Response:\n{last_msg_content}\n"
            + json_prompt
        )
        fmsg = [{"role": "user", "content": full_prompt}]

        temp_msg = self._get_response_raw(
            self.interviewer, fmsg, {}, json=True)
        response_dict = json.loads(temp_msg.messages[-1]["content"])
        feedback = response_dict["feedback"]
        is_correct = response_dict["correctness"]
        score = response_dict["score"]
        assert isinstance(
            feedback, str), "Generation Error in Feedback Agent: Feedback should be a string"
        assert is_correct in [
            True,
            False,
        ], "Generation Error in Feedback Agent: `is_correct` should be a boolean value"
        return feedback, is_correct, score

    def call_hint_agent(self, question, response, feedback):

        chat_history_str = "### Previous Chat History\n\n"
        for message in self.interviewee_messages:
            if message["role"] == "assistant":
                chat_history_str += f"{self.interviewee.name}: {message['content']}\n"
            else:
                chat_history_str += f"You: {message['content']}\n"

        chat_history_str += "\n"

        last_msg_content = chat_history_str + "Question: " + question + \
            "\nResponse: " + response + "\nFeedback: " + feedback

        hint_msg = [
            {
                "role": "user",
                "content": self.hint_prompt_template.format(
                    interviewee_name=self.interviewee.name) + last_msg_content,
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
            last_msg_content = chat_history_str + "\nReference Solution" + \
                self.interviewer.seed_question_answer
        else:
            last_msg_content = chat_history_str

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

        response = self._get_response(self.interviewer, question_msg, {})
        return response.messages[-1]["content"]

    # Note: Please follow the convention of adding the message to the
    # conversation first and then displaying it
    def run(self) -> Dict[str, Any]:
        """Run the interview and return results."""
        self.console.print("\n[info]Starting Interview Session...[/info]\n")
        self.report_manager.start_interview(self.log_file_path)
        initial_message = self.config["session"]["initial_message"]
        self.add_message(self.interviewer, initial_message)
        self.display_message(self.interviewer.name, initial_message)

        context = self.config["session"]["initial_context"]
        response = self._get_response(
            self.interviewee, self.interviewee_messages, context)
        self.add_message(self.interviewee, response.messages[-1]["content"])
        self.display_message(response.agent.name,
                             response.messages[-1]["content"])

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
                messages=[{"role": "assistant",
                           "content": self.interviewer.seed_question}],
                agent=self.interviewer,
                context_variables={},
            )
            self.seed_question_used = True
            self.questions.append(self.interviewer.seed_question)
        else:
            # Generate a question as usual
            interviewer_response = self._get_response(
                self.interviewer, self.interviewer_messages, {})

        response = interviewer_response
        self.add_message(self.interviewer, response.messages[-1]["content"])
        self.display_message(self.interviewer.name,
                             response.messages[-1]["content"])

        while self.questions_count <= self.max_questions:
            # 1. Get response from interviewee
            question = self.interviewer_messages[-1]["content"]
            response = self._get_response(
                self.interviewee, self.interviewee_messages, {}).messages[-1]["content"]
            self.add_message(self.interviewee, response)
            self.display_message(self.interviewee.name, response)

            # 2. Get feedback from feedback agent. Note that the message from
            # feedback agent is not added to the conversation
            feedback, is_correct, score = self.call_feedback_agent(
                question, response)
            self.report_manager.log_attempt(question, 0, score)
            self.feedbacks.append(feedback)
            self.display_message(
                "Feedback Agent",
                feedback +
                ("\n\nCorrectness: True" if is_correct else "\n\nCorrectness: False"),
            )

            # Retry the question `self.max_retries`` times if the response is
            # incorrect
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

                    feedback, is_correct, score = self.call_feedback_agent(
                        question, response)
                    self.report_manager.log_attempt(
                        question, current_retry + 1, score)
                    self.feedbacks.append(feedback)
                    self.display_message(
                        "Feedback Agent",
                        feedback +
                        ("\n\nCorrectness: True" if is_correct else "\n\nCorrectness: False"),
                    )
                    current_retry += 1
                if is_correct == False:
                    # If max retries reached, get next question
                    self.current_retry = None
                    move_on_after_fails = (
                        "I think this question is too difficult for you. Let's move on to the next question."
                    )
                    self.add_message(self.interviewer, move_on_after_fails)
                    self.display_message(
                        self.interviewer.name, move_on_after_fails)

            # Reset the interviewee messages when moving on to the next
            # question
            self.interviewee_messages = []

            self.questions_count += 1
            if self.questions_count <= self.max_questions:
                self.console.print(f"\n[info]Question {self.questions_count}")
                response = self.call_question_agent(
                    self.interviewer, self.interviewer_messages)
                self.questions.append(response)
                self.add_message(self.interviewer, response)
                self.display_message(self.interviewer.name, response)

            # 4. Check end conditions for the interview
            if self.questions_count > self.max_questions:
                final_message = "Maximum number of questions reached. Concluding interview."
                self.console.print(f"\n[warning]{final_message}[/warning]")
                self.interviewer_messages.append(
                    {"role": "assistant", "content": final_message})
                response = self._get_response(
                    self.interviewer, self.interviewer_messages, {
                        "force_conclude": True})
                self.display_message(response.agent.name,
                                     response.messages[-1]["content"])
                break

        results = {
            "score": response.context_variables["score"],
            "feedback": response.context_variables["comments"],
            "questions_asked": self.questions_count - 1,
        }

        self.report_manager.complete_interview(results)
        self.display_results(results)
        return results
