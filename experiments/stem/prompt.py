# prompt.py
from src.utils import extract_json

STEM_ATOMIC_FACT_GENERATOR_PROMPT_TEMPLATE = """
Instructions:
1. You are given a sentence. Your task is to break the sentence down into a list of atomic facts.
2. An atomic fact is a sentence containing a singular piece of information.
3. You should only output the atomic facts as a json format. (Refer below example)
4. Each atomic fact in the outputted list should check a different piece of information.

Example:
INPUT Example:
Raheem Sterling has not signed new Liverpool contract. Sterling gave an interview last week suggesting he might want to leave. But Brendan Rodgers insists the forward has never expressed desire to go.

OUTPUT Example:
{{"1": "Raheem Sterling has not signed new Liverpool contract",
"2": "Sterling gave an interview last week",
"3": "The interview suggests Sterling might want to leave",
"4": "Brendan Rodgers insists Sterling has never expressed desire to go"}}

Input:{input}
Output:
"""

STEM_MODERATOR_STATE_INIT_ADDING_PROMPT_TEMPLATE = """
You are provided with a question and its solution. Your task is to create one unique question based on these.

### Instructions:

1. Create two simple questions:
   - Both questions should be easily answerable from the given solution.

2. Combine the questions:
   - Merge the three questions (second simple question, original question, first simple question) into a single, coherent question in that order.

3. Paraphrase:
   - Rewrite the merged question, ensuring it retains the original meaning.

### Output Format:

{{
  "new_question": [
    "question1",  // First simple question from the reference solution.
    "question2"   // Second simple question from the reference solution.
  ],
  "merged_question": " ",  // The single merged question in the specified order.
  "paraphrased_merged_question": ""  // Paraphrased version of the merged question.
}}

### Input:
Question: {question}
Solution: {solution}
"""

STEM_MODERATOR_STATE_INIT_MODIFYING_PROMPT_TEMPLATE = """
You are provided with a question and its solution. Your task is to create one unique question based on these.

### Instructions:

1. Create one question that is different from the original question:
- The new question should be answerable based on the provided solution, and it should not focus on overly minor details.

### Output Format:

{{
  "new_question": " ",  // The single merged question in the specified order.
  "new_solution": "The relevant section of the original solution that answers the new question."
}}

### Input:
Question: {question}
Solution: {solution}
"""


STEM_MODERATOR_STATE_INIT_PARAPHRASING_PROMPT_TEMPLATE = """Paraphrase the following question to make it as different as possible while retaining its meaning and all the important information. Response in JSON format.
---
Here are examples. Please follow the format as the following expert acts. Your output must be in a json format.
initial question : I'm trying to understand constant acceleration in special relativity. Suppose I'm in a spaceship that starts moving with a constant accerelation of 10m/s^2, creating the illusion of having gravity equivalent to the Earth's onboard. How much time would have passed for outsiders, after I have been traveling for 10 years.
output : {{"revised_question" : "In the context of special relativity, consider a spacecraft accelerating at 10m/s^2, simulating Earth-like gravity for its occupants. If the journey lasts 10 years from the perspective of those on board, how much time will elapse for external observers?"}}
---
initial question : {question}
"""

STEM_EVALUATOR_STATE_EXP_0_PROMPT_TEMPLATE = """
You are provided with a question, a reference solution, the model's output which is divided into atomic fact units, along with their correctiveness.

Your role is to generate the feedback to the model based on the given assessment on reference solution.

Instructions:
1. Provide feedback on the factual accuracy of the model's output: If there are unsupported facts in the reference solution or if the facts differ from the actual facts you know, offer feedback to prompt revision without explicitly stating the error.
2. Never contain any facts of the reference solution to the feedback. Instead, ask questions to verify knowledge.
3. Never mention about "reference solution" in your merged feedback.
3. For facts that are correct but unsupported by the reference answer, no feedback is needed.
4. Generate feedback on assessment: Address issues related to completeness, redundancy, readability, and depth. If the output lacks in any of these areas, provide feedback on how the model can improve.
5. Provide constructive feedback to encourage revision, focusing on guiding the model to improve.

Output Example Format (JSON):
{{
  "feedbacks on factuality": // Provide feedback to encourage revision without revealing the exact error.,
  "feedback on assessment":  // Explain any deficiencies related to completeness, redundancy, readability, or depth that the model may exhibit.,
  "merged_feedback" : // Generate a single, consolidated feedback string for the model to guide the revisions based on the feedback
}}

Question: {question}

Reference Solution: {solution}

Model's Output: {history}

Feedback:
"""


STEM_EVALUATOR_STATE_EXP_PROMPT_TEMPLATE = """You are an expert tasked with evaluating and providing feedback on an assistant's performance.
--- 
Your response should contain the following elements:
1. "status": Indicate whether the answer is "complete" (fully correct), "partially_correct" (some elements are correct but not all), or "incorrect" (entirely wrong).
2. "feedback": Provide specific, constructive feedback based on the differences between the correct solution and the model's output. Your feedback should:
   - Highlight what aspects of the answer are correct (if any).
   - Identify specific areas where the model's output differs from the correct solution, without revealing the entire solution.
   - Offer guidance or hints that can help the model improve its answer, focusing on the concepts or steps that need correction.
   - If the process is incorrect but the final answer is right, explain that the reasoning needs improvement.
   - Encourage the model to think step-by-step and retry if necessary.

Remember:
- Do not give away the complete solution or tell exactly which step is incorrect.
- If it's not the first attempt, provide more detailed hints, such as mentioning a relevant equation or concept, without repeating previous feedback.
- Tailor your feedback to the specific errors or misconceptions evident in the model's output.
- If there is a lack in at least one aspect among completeness, redundancy, readability, or depth, consider it incomplete and provide feedback on the identified shortcomings.
Here are some examples of the expected format and style of feedback:

{{"status": "complete",
"feedback": "Excellent work! Your solution is correct and your reasoning is sound. You've correctly applied [specific concept] and arrived at the right conclusion."}}

{{"status": "incomplete",
"feedback": "You're on the right track with [specific correct aspect], but there's an issue with your approach to [problematic area]. Consider how [relevant concept] applies in this situation. Try revisiting that part of your solution."}}

{{"status": "incomplete",
"feedback": "Your approach needs reconsideration. The key concept you should be focusing on is [relevant concept without giving away the solution]. Think about how this concept applies to the given problem and try to solve it step by step."}}

{{"status": "incomplete",
"feedback": "While your final answer is correct, your process doesn't align with the expected solution. Can you explain your reasoning for [specific step]? Consider if there's a more standard approach to this type of problem."}}

---
Now provide your feedback based on the following information:

Question: 
{question}

Reference Answer (DO NOT disclose this to the assistant): 
{answer}

Correct solution (DO NOT disclose this to the assistant):
{solution}

Previous Feedbacks :
{model_history}

Model output (This is the part to be evaluated): 
{model_output}

Ensure your feedback is unique and does not repeat previous feedback. 
Expert feedback:"""


STEM_EVALUATOR_STATE_INDEPTH_QUESTION_PROMPT_INITIAL_TEMPLATE = """There's initial question and revised question. Some of information from initial question are deleted to revised question. For the given intial question, revised question and deleted information, You are an Evalautor that answer the evaluatee's questions. The evaluatee's role is to find deleted information. If the evaluatee asks for information that corresponds to the deleted information, provide that information. If the evaluatee asks for information not included in the deleted information, respond that this information is not needed. If the evaluatee tries to solve the problem without asking anything, inform them that the information is needed. If the evaluatee has asked for and found all the information in the deleted information, respond the "Status" with  "complete.". Else, respond the "Status" with "incomplete".
---
Here are examples. Please follow the format as the following expert acts. Your output must be a json format.
{output_example}
---
Reference Material : {initial_question}
Dialogue_History : {Dialogue_History}
Evalautor : """


STEM_EVALUATEE_STATE_EXP_PROMPT_TEMPLATE = """Question: {question}"""

STEM_GRADER_0_PROMPT_TEMPLATE = """
You are tasked with evaluating a model's output based on the given question and reference solution.

1. Break down the model's output into atomic facts (distinct units of single information).
2. For each fact, decide if it is correct or incorrect by comparing it to the reference solution, relevance with the question, and provide a short justification.
3. Assess weaknesses based on redundancy, readability, and depth. Use labels (high/middle/low) and brief explanations.

Output format:

{{
  "atomic_facts": [
    {{
      "fact_number": 1,
      "fact": "fact content",
      "relevance" :"yes/no"
      "decision": "correct/incorrect",
      "justification": "short explanation"
    }},
    ...
  ],
  "assessment": {{
    "completeness": {{
      "label": "high/middle/low",
      "description": "Determines whether the solution addresses all aspects and components of the question. If not, explain which points are missing or insufficient."
    }}
    "redundancy": {{
      "label": "high/middle/low",
      "description": "Measures if the solution contains unnecessary repetition or irrelevant information."
    }},
    "readability": {{
      "label": "high/middle/low",
      "description": "Evaluates how clear, well-organized, and easy to follow the solution is."
    }},
    "depth": {{
      "label": "high/middle/low",
      "description": "Assesses how thoroughly the student has explored the problem and provided detailed reasoning."
    }}

  }}
}}

### Inputs:
- Question: {question}
- Reference Solution: {solution}
- Model's Output: {history}

### Output:
"""

STEM_GRADER_1_PROMPT_TEMPLATE = """Task:
You are given a question, a reference solution, and the model's output, which is broken down into atomic fact units, along with their correctness and justification.
The model has revised the incorrect parts of its original output, and these revisions are provided in the model's correction statement.

Your task is to update the model's original output by replacing the corresponding revised facts with those found in the model's correction statement. 
Ensure that updated facts are from model's correction statement, not the reference solution.
For facts that were not revised, maintain the same content and correctness as before, so that your output contains the same number of atomic facts as the model's original output. 

Output format:
{{
  "atomic_facts": [
    {{
      "fact_number": 1,
      "fact": "fact content, change if the fact is revised by the model. else maintain the same",
      "relevance": "yes/no",
      "decision": "correct/incorrect",
      "justification": "brief explanation"
    }},
  ],
  "assessment": {{
    "completeness": {{
      "label": "high/middle/low",
      "description": "Determines whether the solution addresses all aspects and components of the question. If not, explain which points are missing or insufficient."
    }}
    "redundancy": {{
      "label": "high/middle/low",
      "description": "Measures if the solution contains unnecessary repetition or irrelevant information."
    }},
    "readability": {{
      "label": "high/middle/low",
      "description": "Evaluates how clear, well-organized, and easy to follow the solution is."
    }},
    "depth": {{
      "label": "high/middle/low",
      "description": "Assesses how thoroughly the student has explored the problem and provided detailed reasoning."
    }}

  }}
}}

Input:
Question: {question}
Solution: {solution}
Previous Feedback: {feedback}
Model's original output with correctness: {history}
Model's correction statement: {correction}
Output:
"""

STEM_GRADER_0_RECALL_PROMPT_TEMPLATE = """

You are given two inputs:

1. Reference Solution: A list of atomic facts that serve as the ground truth or correct answer.
2. Model's Output with correctness: A generated atomic facts from the model and the assessment on it.

Your task is to evaluate if each fact from the Reference Answer is supported by the Model's Output. 
1. For each fact, annotate whether it is supported or unsupported based on whether the Model's Output sufficiently covers that fact. 
2. The facts of Reference Answer does not need to be explicitly supported by the Model's output, but should be strongly implied by the Model's output.
3. As part of your reasoning, contains the corresponding part of the Model's output.

Output your evaluation only in the json format:
  {{
    "reference_facts":
    {{
      "1": {{
        "fact": "Atomic fact from the reference answer",
        "reasoning": "Corresponding part of the model's output (if supported)",
        "label": "supported or unsupported",
      }},
      "2": {{
        "fact": "Atomic fact from the reference answer",
        "reasoning": "Corresponding part of the model's output (if supported)",
        "label": "supported or unsupported",
      }}
    }}
  }}


Now, evaluate the facts based on the provided reference answer and the model's output.
Question : {question}
Reference Solution : {solution}
Model's output : {history}
Output : 
"""

STEM_GRADER_1_RECALL_PROMPT_TEMPLATE = """

You are given three inputs:

1. Reference Solution: A dictionary of atomic facts serving as the ground truth or correct answer. For each fact, there is an annotation label indicating whether it is supported or unsupported, based on whether the model’s output sufficiently covers that fact.
2. Your Previous Feedback: Feedback you previously provided on the model’s output for the given question.
3. Model’s Correction Statement: Based on your previous feedback, the model has revised the incorrect parts of its original output. These revisions are presented in the model's correction statement.

Instruction:
Your task is to update the annotation labels and reasoning in the Reference Solution to reflect the revised facts found in the Model’s Correction Statement. Follow these guidelines:

1. Ensure that updated facts are derived from the Model’s Correction Statement.
2. For facts that were not revised, retain their content and correctness as before, so that the total number of atomic facts remains consistent.
3. The facts in the Reference Solution do not need to be explicitly stated in the model’s output, but they should be strongly implied.
4. Provide detailed reasoning before showing your final output. Include specific references to the Model’s Correction Statement as part of your reasoning.

Output your evaluation only in the json format:
```json
  {{
    "reference_facts":
    {{
      "1": {{
        "fact": "Atomic fact from the reference answer",
        "reasoning": "Corresponding part of the model's output (if supported)",
        "label": "supported or unsupported",
      }},
      "2": {{
        "fact": "Atomic fact from the reference answer",
        "reasoning": "Corresponding part of the model's output (if supported)",
        "label": "supported or unsupported",
      }},
      ...
    }}
    }}
```

Now, evaluate the facts based on the provided reference answer and the model's output.
Input:
Question: {question}
Reference Solution: {solution}
Previous Feedback: {feedback}
Model's correction statement: {correction}
Output:
"""
# STEM_GRADER_0_RECALL_PROMPT_TEMPLATE  = """
# You are tasked with evaluating a model's output based on the given question and reference solution.

# 1. Break down the reference solution into atomic facts (Distinct units of single information. Single sentence can divide into several atomic facts).
# 2. Break down the model's output into atomic facts.
# 2. For each atomic fact generated by the model, determine if it is correct or incorrect by comparing it against the reference solution. Additionally, evaluate whether the fact is covered in the reference solution or not, and provide a brief justification for your decision.
# 3. Assess weaknesses based on redundancy, readability, and depth. Use labels (high/middle/low) and brief explanations.

# Output format:

# {{
#   "solution_atomic_facts": [
#     {{
#       "fact_number": 1,
#       "fact": "" // atomic fact of the reference solution
#     }},
#   ],
#   "model_atomic_facts": [
#     {{
#       "fact_number": 1,
#       "fact": "fact content",
#       "reference solution coverage": "yes/no", // whether the fact is covered in the reference solution or not
#       "decision": "correct/incorrect",
#       "justification": "short explanation"
#     }},
#     ...
#   ],
#   "assessment": {{
#     "completeness": {{
#       "label": "high/middle/low",
#       "description": "Determines whether the solution addresses all aspects and components of the question. If not, explain which points are missing or insufficient."
#     }}
#     "redundancy": {{
#       "label": "high/middle/low",
#       "description": "Measures if the solution contains unnecessary repetition or irrelevant information."
#     }},
#     "readability": {{
#       "label": "high/middle/low",
#       "description": "Evaluates how clear, well-organized, and easy to follow the solution is."
#     }},
#     "depth": {{
#       "label": "high/middle/low",
#       "description": "Assesses how thoroughly the student has explored the problem and provided detailed reasoning."
#     }}

#   }}
# }}

# ### Inputs:
# - Question: {question}
# - Reference Solution: {solution}
# - Model's Output: {history}

# ### Output:
# """
STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_PROMPT_TEMPLATE = """
You are given two inputs:

1. Question: The original question that was asked.
2. Reference Answer: A list of atomic facts with labels indicating whether each fact is supported or unsupported by a model’s output.

Instruction:
1. Your task is to generate follow-up questions based on the atomic facts from the Reference Answer that were labeled as unsupported by the model's output. 
2. The follow-up questions should be designed to test whether the model understands the unsupported facts.
3. Never contain any facts of the reference solution to the question. Instead, ask questions to verify knowledge.
4. The questions should indirectly reference the concepts in a way that allows us to assess the model’s understanding.

Your follow-up questions should not simply ask the fact directly but should guide the model to demonstrate whether it knows the fact.


Output your evaluation only in the json format:
Input example:
{{
  "1": {{
    "fact": "Variables are used to store data that can be used in the program",
    "label": "supported",
    "part of the model": "Variables hold data for use within the program"
  }},
  "2": {{
    "fact": "Data Types define the type of data that can be stored in variables",
    "label": "supported",
    "part of the model": "Data types determine the kind of data stored in variables"
  }},
  "3": {{
    "fact": "Data Types include integers and strings",
    "label": "unsupported",
    "part of the model": ""
  }},
  "4": {{
    "fact": "Operators perform operations on variables and values",
    "label": "unsupported",
    "part of the model": ""
  }}
}}

Example Output(json):

{{ "follow-up question" : {{
  "3": {{
    "follow-up question": "Can you give some examples of different data types that can be used in a program?"
  }},
  "4": {{
    "follow-up question": "How would you perform basic operations like addition or comparison on variables in a program?"
  }}
}}
  "merged_question" : // Merge the follow-up question provided above into a single, consolidated question string to guide the model's answer based on the question
}}
}}


Now, based on the unsupported facts, generate follow-up questions to assess the model's understanding.
Question : {question}
Reference Answer : {solution}
Output : 
"""
STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_1_PROMPT_TEMPLATE = """
You are tasked to evaluate and provide feedback on the model's output for follow-up questions related to an initial question. 
The follow-up includes individual questions as well as a merged question (a combination of all the follow-up questions). 
You need to assess the correctness of the model's output for each question and provide overall feedback.

Instruction:

1. Evaluate the correctness of the model's output for each follow-up question, referencing the provided solution. 
2. When generating overall feedback, focus on factual accuracy and clarity of the model's output.
3. If you identify unsupported or incorrect facts based on your own knowledge or if the reference solution contains inconsistencies, ask guiding questions to prompt revision. Do not directly state any errors.
4. Do not include any facts from the reference solution in your feedback. Instead, ask open-ended questions to encourage the model to verify and clarify its responses.
5. Provide constructive feedback that encourages the model to refine its answers, with a focus on improving accuracy and completeness.

Feedback Output Example(json):
{{ "follow-up question" : {{
  "3": {{
    "follow-up question": "Can you give some examples of different data types that can be used in a program?",
    "correctness": "correct/incorrect // Evaluate correctness of model's output on this question",
    "justification": "Your justification"
  }},
  "4": {{
    "follow-up question": "How would you perform basic operations like addition or comparison on variables in a program?"
    "correctness": "correct/incorrect // Evaluate correctness of model's output on this question",
    "justification": "Your justification"
  }}
}},
  "feedback" :" // Provide feedback to encourage revision without revealing the exact error to guide the model's revisions based on the feedback",
}}
}}

Now, generate the feedback based on inputs:
Initial Question : {question}
Reference Answer : {solution}
Followup Question : {followup}
Model's Output : {history}
Your Evaluation Output:
"""

STEM_EVALUATOR_STATE_FOLLOWUP_QUESTION_2_PROMPT_TEMPLATE = """
You are tasked to evaluate and provide feedback on the model's output for follow-up questions related to an initial question. 
The follow-up includes individual questions as well as a merged question (a combination of all the follow-up questions). 
You need to assess the correctness of the model's output for each question and provide overall feedback.


Instruction:
Update the correctness labels and justifications in Evaluation on Model's previous output based on the Model's Correction Statement for each follow-up question, referencing the provided solution.:
1. Ensure updated facts come from the Model’s Correction Statement.
2. For revised facts, re-evaluate and update the corresponding atomic fact, justification, and correctness label.
4. Retain unchanged facts and correctness labels as they are.
5. While the reference solution may guide your evaluation, it is not necessary to match it exactly.

Feedback Output Example(json):
{{ "follow-up question" : {{
  "3": {{
    "follow-up question": "Can you give some examples of different data types that can be used in a program?",
    "correctness": "correct/incorrect // Evaluate correctness of model's output on this question",
    "justification": "Your justification"
  }},
  "4": {{
    "follow-up question": "How would you perform basic operations like addition or comparison on variables in a program?"
    "correctness": "correct/incorrect // Evaluate correctness of model's output on this question",
    "justification": "Your justification"
  }}
}},
  "feedback" :" // Provide feedback to encourage revision without revealing the exact error to guide the model's revisions based on the feedback",
}}
}}

Now, generate the feedback based on inputs:
Initial Question : {question}
Reference Solution : {solution}
Followup Question : {followup}
Previous Feedback: {feedback}
Evaluation on Model's previous output: {history}
Model's correction statement: {correction}
Your Evaluation Output:

"""
STEM_GRADER_0_PRECISION_PROMPT_TEMPLATE = """
You are tasked with evaluating a model's output based on the given question and reference solution.

1. Decompose the model’s output into individual atomic facts. An atomic fact is a sentence containing a singular piece of information.
2. For each atomic fact, evaluate its accuracy as either correct or incorrect, and give a brief justification for your assessment.
3. While the reference solution may guide your evaluation, it is not necessary to match it exactly.
4. Identify weaknesses in the output based on redundancy, readability, and depth, assigning labels (high/middle/low) to each, along with a short explanation.

Output format:

{{
  "model_atomic_facts": [
    {{
      "fact_number": 1,
      "fact": "fact content",
      "justification": "short explanation",
      "correctness": "correct/incorrect",
      "reference solution coverage": "supported/unsupported", // whether the fact is supported by the reference solution or not
    }},
    ...
  ],
  "assessment": {{
    "completeness": {{
      "label": "high/middle/low",
      "description": "Determines whether the solution addresses all aspects and components of the question. If not, explain which points are missing or insufficient."
    }}
    "redundancy": {{
      "label": "high/middle/low",
      "description": "Measures if the solution contains unnecessary repetition or irrelevant information."
    }},
    "readability": {{
      "label": "high/middle/low",
      "description": "Evaluates how clear, well-organized, and easy to follow the solution is."
    }},
    "depth": {{
      "label": "high/middle/low",
      "description": "Assesses how thoroughly the student has explored the problem and provided detailed reasoning."
    }}

  }}
}}

### Inputs:
- Question: {question}
- Reference Solution: {solution}
- Model's Output: {history}

### Output:
"""


STEM_GRADER_1_PRECISION_PROMPT_TEMPLATE = """
You are tasked with evaluating a model's output based on the given question and reference solution.

Input:
1. Reference Solution: A dictionary of atomic facts serving as the ground truth or correct answer. For each fact, there is an annotation label indicating whether it is supported or unsupported, based on whether the model’s output sufficiently covers that fact.
2. Model's original output with correctness: Model's previous output and it assessment.
3. Previous Feedback: The Feedback that you gave to Models' previous output.
3. Model’s Correction Statement: Based on your previous feedback, the model has revised the incorrect parts of its original output. These revisions are presented in the model's correction statement.

Instruction:
Update the correctness labels and justifications in the Model's original output based on the Model's Correction Statement:
1. Ensure updated facts come from the Model’s Correction Statement.
2. For revised facts, re-evaluate and update the corresponding atomic fact, justification, and correctness label.
3. For newly added facts, include them as new atomic facts with correctness labels and justifications.
4. Retain unchanged facts and correctness labels as they are.
5. While the reference solution may guide your evaluation, it is not necessary to match it exactly.
6. Re-Identify weaknesses in the revised output based on redundancy, readability, and depth, assigning labels (high/middle/low) to each, along with a short explanation.

Output format:

{{

  "model_atomic_facts": [
    {{
      "fact_number": 1,
      "fact": "fact content, change if the fact is revised by the model. else maintain the same",
      "reference solution coverage": "yes/no", // whether the fact is covered in the reference solution or not
      "correctness": "correct/incorrect",
      "justification": "brief explanation"
    }},
  ],
  "assessment": {{
    "completeness": {{
      "label": "high/middle/low",
      "description": "Determines whether the solution addresses all aspects and components of the question. If not, explain which points are missing or insufficient."
    }}
    "redundancy": {{
      "label": "high/middle/low",
      "description": "Measures if the solution contains unnecessary repetition or irrelevant information."
    }},
    "readability": {{
      "label": "high/middle/low",
      "description": "Evaluates how clear, well-organized, and easy to follow the solution is."
    }},
    "depth": {{
      "label": "high/middle/low",
      "description": "Assesses how thoroughly the student has explored the problem and provided detailed reasoning."
    }}

  }}
}}

Input:
Question: {question}
Reference solution: {solution}
Previous Feedback: {feedback}
Model's original output with correctness: {history}
Model's correction statement: {correction}
Output:
"""

# STEM_GRADER_1_RECALL_PROMPT_TEMPLATE  = """
# You are given the Question, Reference solution and Model's answer on it. Compare the Reference solution with Models' answer and verify the facts that are in Reference solution but not answered by model.

# Output format:

# {{

#   "facts": [
#     {{
#       "fact_number": 1,
#       "fact": "fact that are covered in Reference Answer but not in Models' answer",
#     }},

# Input:
# Question: {question}
# Reference solution: {solution}
# Model's output: {answer}
# Output:
# """

STEM_EVALUATOR_STATE_UNC_PROMPT_TEMPLATE = """There is an initial question and a revised question. Some information from the initial question has been deleted in the revised question. For the given initial question, revised question, and deleted information, you are an Evaluator that answers the evaluatee's questions. The evaluatee's role is to find the deleted information.
If the evaluatee asks for information that corresponds to the deleted information, provide that information.
If the evaluatee attempts to solve the problem without asking anything, inform the model to find additional information, without providing the deleted information.
If the evaluatee continues to fail, then provide the exact information.
If the evaluatee has asked for and found all the information in the deleted information, respond with Status as complete. Otherwise, respond with Status as incomplete.
---
Here are examples. Please follow the format as the following expert acts. Your output must be a json format.
{{'initial_question' : How do you calculate the proper time experienced by an observer moving at a constant acceleration? The proper time (Δτ) is related to the time Δt measured by a stationary observer by the formula: Δτ = Δt * sqrt(1 - v²/c²), where v is the velocity of the moving observer and c is the speed of light.
'revised_question' : How do you calculate the proper time experienced by an observer moving at a constant acceleration?,
'deleted_information' : ["The proper time (Δτ) is related to the time Δt measured by a stationary observer by the formula: Δτ = Δt * sqrt(1 - v²/c²), where v is the velocity of the moving observer and c is the speed of light."]}}
{{'Dialogue_History' : ["Evalautee : The proper time is calculated using the Lorentz factor."]
Evalautor : {{"answer" : "You need additional information to solve this problem. Can you find which specific information is needed?",
"status" : "incomplete"}},
{{'Dialogue_History' : ["Evalautee : What is the formula for calculating proper time?"]
Evalautor : {{"answer" : "The proper time (Δτ) is related to the time Δt measured by a stationary observer by the formula: Δτ = Δt * sqrt(1 - v²/c²), where v is the velocity of the moving observer and c is the speed of light.",
"status" : "Complete"}},

}}
---
initial_question : {initial_question}
revised_question : {revised_question}
deleted_information : {deleted_information}
Dialogue_History : {Dialogue_History}
Evalautor : """
