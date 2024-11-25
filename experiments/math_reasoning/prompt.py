# prompt.py
from src.utils import extract_json

MATH_MODERATOR_STATE_INIT_UNCLARIFYING_PROMPT_TEMPLATE = """You are given a mathematical expression where key information must be removed, but the remaining structure and operations should not change. Only remove critical data that makes the problem unsolvable without that information.

Guidelines:
1. Remove only key information required for the solution (e.g., constants, values) without changing the operations and convert to unknown variables or ambiguous words.
2. Ensure the revised question retains the same structure and other information.
3. Avoid removing trivial or subtle details.
4. Do not modify the mathematical operations or alter the structure of the equation.
5. In the explanation, detaily explain **exactly how and where deleted information fits into the equation or text**. 
For example, explain which unknown variable or ambigous words denote what value.   
Please respond in the following JSON format:

Example 1:
output: {{
    "initial_question": "Find the value of $: 3[6-3(2)]\\mul2 -4$."
    "deleted_information": "x=6",
    "explanation": "6 in the quare brackets is converted to unknown variable x.",
    "revised_question": "Find the value of $: 3[x-3(2)]\\mul2 -4$."
}}

Example 2:
output: {{
  "initial_question": "A cell-phone recharges at the rate of 1 percentage point per 3 minutes. Now, the phone is at 60% charge. How long will it take to fully charge, in hours?",
    "deleted_information": "cell-phone recharges at the rate of 1 percentage point per 3 minutes.",
    "explanation": "The rate of charging 1 percentage point per 3 minutes is converted to "certain rate".",
    "revised_question": "The cell-phone recharges at a certain rate. Now, the phone is at 60% charge. How long will it take to fully charge, in hours?"
}}


Initial question(Remove the information and do not change other information or operations): {question}"""
# """
# Task : Remove some critical information from the "initial_question" and set the modified question as "revised_question." The revised question should not be solvable without the deleted information.
# The equation is in latex format.

# Guidelines:
# 1. Remove only key information required for the solution, but retain other details that preserve the structure of the problem.
# 3. Avoid removing trivial or subtle details.
# 4. After removal, ensure the revised question remains natural and understandable.

# Response format must be in JSON as shown below.

# Examples:

# Example 1:
# initial_question: "Find the value of $: 3[6-3(2)]\\mul2 -4$."
# output: {{
#     "deleted_information": "x=6",
#     "explanation": "deleted 6 and converted to unknown variable x. Other operations and information remain same",
#     "revised_question": "Find the value of $: 3[x-3(2)]\\mul2 -4$."
# }}

# Example 2:
# initial_question: "A cell-phone recharges at the rate of 1 percentage point per 3 minutes. Now, the phone is at 60% charge. How long will it take to fully charge, in hours?"
# output: {{
#     "deleted_information": "cell-phone recharges at the rate of 1 percentage point per 3 minutes.",
#     "explanation": "Removed the rate of charging to require the agent to inquire about it.",
#     "revised_question": "The cell-phone recharges at a certain rate. Now, the phone is at 60% charge. How long will it take to fully charge, in hours?"
# }}


# Initial question (Remove the information and do not change other information or operations): {question}

# Output:
# """


MATH_MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE = """
You are tasked with paraphrasing the following question to make it as different as possible while retaining all the important information. The paraphrased question should retain the same meaning, but be phrased differently. Do not omit any key information. Response must be in JSON format.

Guidelines:
1. Ensure the paraphrased question keeps all the original information (without changing any operation) but rewords it significantly.
2. Do not add extra information or change any symbols.

Response format must be in JSON as shown below.

Example :
initial_question: "A cell-phone recharges at the rate of 1 percentage-point of charge per 3 minutes. Now, the phone is at 60% charged. How long will it take to fully charge, in hours? Solution output format: an integer."
output: {{
    "revised_question": "The battery of a phone increases by 1% every 3 minutes. If the current charge is 60%, how many hours will it need to become fully charged? Solution output format: an integer."
}}

Initial question (Paraphrase only this part): {question}

Output:
"""

MATH_EVALUATOR_STATE_UNC_0_PROMPT_TEMPLATE = '''Task: Provide feedback on the model's answer. The model was given a revised question with some information deleted from the initial question, and solved the problem without knowing that fact. The initial question, revised question, and deleted information are provided below.

Looking at the model's output, categorize the model's response as follows:
- it asks for the necessary information
- it already know the deleted information (e.g. the exact value of unknown variable )
- it solve the problem by assuming the deleted information differently from the original information.

Response format must be in JSON as shown below.

{{“category”:”it already know the deleted information”, “explanation”:[explanation on it]}}

Now generate the feedback
initial_question: {initial_question}
revised_question : {revised_question}
explanation : {explanation}
deleted_information (This is the information that evaluatee needs to solve the question): {deleted_information}
Model output (This is the only part to be evaluated):
{Dialogue_History}

Expert feedback:"""
'''

MATH_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE = """
Task: Generate response to the Model output below. The model was given and solved a revised question with some information from the initial question converted to unknown variable or ambigous words.
Your job is to generate feedback that informs about the missing information and encouraging them to rearrange the question based on the missing information and solve the problem again. 

### Guidelines:
- When explaining the deletion, clearly specify **what information was deleted**, and **exactly how and where it fits into the equation or text**.
- If the model assumeed the deleted information differently from the original information, correct that information. 
- If the model solved the problem without knowing certain information, let it know that [deleted information], clearly specify **exactly how and where it fits into the equation or text**.
- For example, if the specific information converted to unknown variable x or ambiguous words such as "certain rate", mention the which value was for unknow variable.   
- DO NOT disclose any hint or the correct solution to the model.
- If you provide the evaluatee with the deleted information, respond with the status as "complete." Otherwise, respond with the status as "incomplete."

Response format must be in JSON as shown below.
Example output: {{
    "deleted_information": "x=6",
    "explanation": "6 in the square brackets is converted to unknown variable x.",
    "revised_question": "Find the value of $: 3[x-3(2)]\\mul2 -4$."
    "feedback": "To reach to the final answer, you need exact value of x = 6.",   
    "status": "complete"
}}

initial_question: {initial_question}
revised_question : {revised_question}
explanation : {explanation}
deleted_information (This is the information that evaluatee needs to solve the question): {deleted_information}
Analysis on Model’s output (Refer when generating the feedback): {feedback}
Model output (This is the only part to be evaluated): {Dialogue_History}
Explain **exactly how and where it fits into the equation or text**.
Expert feedback:"""


MATH_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE = """
Task: Refer the pre-generated evaluation on given question below, and generate the feedback for the model. 
---
Your response should reflect the evaluations provided without giving away the solution or pinpointing the exact incorrect steps. Use the evaluations to generate constructive feedback. Encourage the assistant to solve the problem again if the answer or process is incorrect, without offering specific hints.

### Guidelines:
- Do not reveal the solution; guide the assistant to understand the correct approach.
- If the model seems to misinterpret the question exactly, tell what the question is again.
- If the answer or process is incorrect, inform the which is incorrect,[answer/process], and encourage a retry without giving specific hints.
- If the process is correct but missing the final answer, prompt them to complete the solution with the final result.


Response format must be in JSON as shown below.

Examples:

Example 1:
{{
    "status": "complete",
    "feedback": "This is GOOD. You have got the solution!"
}}

Example 2:
{{
    "status": "incomplete",
    "feedback": "Your answer is incorrect. The process is correct. Think step by step and try again."
}}

Example 3:
{{
    "status": "incomplete",
    "feedback": "Your approach is generally correct, but you need to reach the final number. Review your steps and solve again."
}}

Now provide your feedback:
Question: {question}
Reference solution (DO NOT disclose): {solution}
Correct answer (DO NOT disclose): {answer}
Pre-generated Evaluation: {evaluation}
Previous Feedback: {model_history}
Model output (to evaluate): {model_output}"""


MATH_EVALUATOR_STATE_EXP_1_PROMPT_TEMPLATE = """
Task: Refer the pre-generated evaluation on given question below, and generate the feedback for the model. 

Your response must include:
- **feedback**: Concise, constructive guidance based on the evaluation and reference solution.
- **feedback_type**: Choose one of the following:
  1. **Conceptual Guidance**: Focus on understanding key concepts.
  2. **Error Identification and Correction**: Addres specific mistakes and guide corrections.
  3. **Process and Strategy Guidance**: Improve the model’s approach or strategy.
  4. **Precision and Accuracy Emphasis**: Stress precision in calculations or answer format.
  5. **Encouragement and Affirmation**: Motivate and reinforce correct actions.

### Guidelines:
- Do not reveal the solution. Guide the assistant toward understanding the correct approach.
- Ensure feedback is unique, avoiding repetition.
- Provide progressively more specific hints without focusing on trivial issues.
- If the model seems don't know about the question exactly, tell what the question is.

### Example Feedback:

Example 1:
```json
{{
  "feedback": "Your answer is correct, but the solving process is flawed. [Explain what's wrong]",
  "feedback_type": "Process and Strategy Guidance"
}}
Example 2:
{{
  "feedback": "Your approach is good, but ensure the final number matches the expected result.",
  "feedback_type": "Precision and Accuracy Emphasis"
}}

Now provide your feedback:
Question: {question}
Reference solution (DO NOT disclose): {solution}
Correct answer (DO NOT disclose): {answer}
Pre-generated Evaluation: {evaluation}
Previous Feedback: {model_history}
Model output (to evaluate): {model_output}"""

MATH_EVALUATOR_STATE_INDEPTH_CONCEPT_QUESTION_PROMPT_TEMPLATE = '''
You are an evaluator assessing the Evaluatee model. For the question provided below, the Evaluatee model gives an explanation of the concept. Your task is to evaluate whether the model understands the concept well, including both the equation and its meaning. Avoid giving away the solution. 
Don't point out things that are too trivial or subtle.
If the model seems to understand the concept well, respond with the status as "complete."
If the model does not understand the concept correctly, respond with the status as "incomplete."
Sample response:

{{"status": "complete", "feedback": "You are understanding the concept needed to solve the question."}}
{{"status": "incomplete", "feedback": "You lack understanding of the concept. [Explain the part that was misunderstood]."}}
---
Now provide your feedback.
Question : {question}
Dialouge History : {Dialogue_History}
Evluatee Model's Output (This is the only part to be evaluated): {response}
Correct answer (please DO NOT disclose the correct solution to the assistant):
{answer}
Reference solution (please DO NOT disclose the correct solution to the assistant):
{solution}
Evalautor : """
'''
MATH_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE = """You are a question generator for assessing the model. Below are the list of the answer history of a Evaluatee model that keeps getting the question wrong, its error type, the corresponding problem, and the solution. 
Model's Error Type is {error_type}. See below and generate proper follow-up question. Do not disclose the error_type to model.

Possible Error Type
1. concept: This error type indicates the model lacks of the concept used to solve the problem. In this case, The feedback should contain the question that can check the understanding of the concept. (e.g. What is the pythagoream theorem?)
2. misinterpret: The model misunderstood or misinterpreted the question. In this case, the feedback should include a follow-up question or clarification that helps the model reassess and correctly interpret the original question. This ensures the model understands the context and requirements before proceeding.
3. calculation: The model made a mistake in calculation.
4. N/A: None of the above, I have a different description.
Sample response:
{{"error_type" : "concept", "feedback" : "It seems that you lack the concept of the Pythagorean theorem. [Request for explaining about the Concept]"}}
{{"error_type" : "misinterpret", "feedback" : "It seems that you misinterpreted the question. [Request for explaining about the meaning of the question]"}}
{{"error_type" : "calculation", "feedback" : "It seems that you made a minor calculation. [Tell the part to be recalculated]"}}
---
Now provide your feedback.
Question : {question}
Correct answer (please DO NOT disclose the correct solution to the assistant):
{answer}
Reference solution (please DO NOT disclose the correct solution to the assistant):
{solution}
Dialogue_History : {Dialogue_History}
Model's Error_Type: {error_type}
Evalautor : """

MATH_EVALUATOR_STATE_INDEPTH_REASK_QUESTION_PROMPT_TEMPLATE = """You are an evaluator assessing the Evaluatee model. The Evaluatee model is attempting to explain the meaning of a question. Your task is to determine whether the Evaluatee model correctly understands the question or not. Avoid giving away the solution. Don't point out things that are too trivial or subtle.
If the model correctly understands the question, respond with the status as "complete."
If the model does not understand the question correctly, respond with the status as "incomplete."

Sample response Examples:
{{"status": "complete", "feedback": "You are understanding the initial question correctly."}}
{{"status": "incomplete", "feedback": "You misunderstood part of the question. [explain the part that was misunderstood]."}}
---
Question : {initial_question}
Correct answer (please DO NOT disclose the correct solution to the assistant):
{answer}
Reference solution (please DO NOT disclose the correct solution to the assistant):
{solution}
Dialouge History : {Dialogue_History}
Evluatee Model's Output (This is the only part to be evaluated): {response}
Evalautor : """

MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_1_QUESTION_PROMPT_TEMPLATE = """You are an evaluator assessing the Evaluatee model. The Evaluatee has successfully answered the problem, and the following is the Evaluatee's solution. Your role is to determine whether the Evaluatee truly understands their solution or if they arrived at the answer through memorization without proper understanding. To do this, you should ask questions that can assess the model's understanding of its own solution. 

Guidelines:
If there are errors or missing steps in Evaluatee's solution, ask questions to clarify or correct these issues.
If there are no errors in the solution, ask questions to confirm the Evaluatee's understanding of the solution steps.
Generate one question and provide the answer in JSON format. Be sure not to ask questions that are already present in thae previous history below.
Create the question soley based on the model's solution.

Sample response Examples:
In the type, write what type your question belongs to. 
{{"question" : "How did you use the Pythagorean theorem to determine that the height of the triangle is 4 units?",
"answer": "The triangle formed by the perpendicular is a right triangle with a hypotenuse of 5 units (one of the original sides) and a base of 3 units (half of the 6-unit side). Using the Pythagorean theorem, ℎ 2 + 3 2 = 5 2 h 2 +3 2 =5 2 , we find ℎ 2 = 25 − 9 = 16 h 2 =25−9=16, so ℎ = 4 h=4 units. ",
"type": "missing_step"}}

initial_question: {initial_question}
Correct answer (please DO NOT disclose the correct solution to the assistant):
{answer}
Reference solution (please DO NOT disclose the correct solution to the assistant):
{solution}
model's solution : {model_solution}
previous history: {Dialogue_History}

Now provide your feedback in JSON format 
Ensure your question does not repeat previous history. Try to ask about different solving steps with previous history. :
Evaluator:"""
MATH_EVALUATOR_STATE_INDEPTH_SUCCESS_0_QUESTION_PROMPT_TEMPLATE = """You are an evaluator assessing the Evaluatee model. The Evaluatee has successfully answered the problem. The initial question, reference solution and model's solution are given below. 
To determine whether the Evaluatee truly understands their solution or if they arrived at the answer through memorization without proper understanding, Evaluatee was asked of the questions from its own solution, which is denoted as follow-up question below.
Your job is to assess the model output of follow-up question. You can refer the reference solution for follow-up question below for evaluation. Don't point out things that are too trivial or subtle.
--- 
Your response should contain the correctness as "status", whether it is correct or wrong, and the feedback. If the model seems to understand the concept in follow-up question that is needed to solve the initial question, regards it as complete. If model's output is generally correct but contains some errors, regards it as partially_complete. Do not give away the solution. 
Here are examples. Please follow the format as the following expert acts.
{{"status" : "complete",
"feedback" : "Your explanation is good.[explain the reason]"}},
{{"status" : "incomplete",
"feedback" : "It seems that you generally do not fully understand the concept. Would you like to explain again?"}},
{{"status" : "partially_complete",
"feedback" : "Your explanation is generally correct, but it seems insufficient to judge whether you have fully understood [mention the insufficient point from the explanation]. Could you explain it a bit more?""}}
---
Now provide your feedback.
Initial Question : 
{initial_question}
Correct answer (please DO NOT disclose the correct solution to the assistant):
{seed_answer}
Reference solution for initial question (please DO NOT disclose the correct solution to the assistant):
{solution}
Model's solution : {model_solution}
Follow-up question : {question}
Reference solution for Follow-up question : {answer}
Model output on Follow-up question (This is the only part to be evaluated): 
{model_output}
Expert feedback:"""

# MATH_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE = """You are a helpful assistant assigned with the task of problem-solving.  To achieve this, you can proactively ask user to give additional information. At each turn, you should provide your step-by-step thinking for solving the task. You have chances to interact with the environment or propose a solution and answer.

# Question: {question}"""

MATH_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE = """Question: {question}"""

MATH_GRADER_PROMPT_TEMPLATE = """Task: You are provided with a model’s output, a reference solution, and a correct answer. Your goal is to determine the correctness of the model's output by comparing it with the reference solution and the correct answer. Note that the reference solution is just a guide—there could be other valid methods to solve the problem.

Please return the evaluation in the following JSON format, which includes the correctness of the model’s final answer and the correctness of the solving process, explanation and it's error type.
Possible Error Types are:
1. concept: This error type indicates the model lacks of the concept used to solve the problem. In this case, The feedback should contain the question that can check the understanding of the concept. (e.g. What is the pythagoream theorem?)
2. misinterpret: The model misunderstood or misinterpreted the question. In this case, the feedback should include a follow-up question or clarification that helps the model reassess and correctly interpret the original question. This ensures the model understands the context and requirements before proceeding.
3. calculation: The model made a mistake in calculation.
4. N/A: None of the above

Response Format:
{{
  "explanation": "<detailed explanation of evaluation>",
  "answer correctness": "<True/False>",
  "solving process correctness": "<True/False>"
  "error type":<concept/misinterperet/calculation/NA>
}}

Initial question : {question}
Correct answer : {answer}
Reference solution : {solution}
Model's Ouput : {history}
"""
