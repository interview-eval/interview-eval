# interview-eval

An automated interview evaluation system that simulates technical interviews using AI agents. The system consists of an AI interviewer and interviewee, conducting structured conversations based on predefined rubrics and strategies.

## 📦 Installation

```bash
pip install interview-eval
```

## ⚙️ Configuration

Create a YAML configuration file with the following structure:

```yaml
interviewer:
  name: "Technical Interviewer"
  model: "model name"
  client:
    api_key: ${OPENAI_API_KEY}
  instructions: "Your interview guidelines..."
  rubric: "Evaluation criteria..."
  
  strategy:
    policy: [...]
    follow_up_rules: [...]
  seed_question: [...]
  rubric: [...]

interviewee:
  name: "Candidate"
  model: "model name"
  client:
    api_key: ${OPENAI_API_KEY}
  instructions: "Interviewee behavior guidelines..."

session:
  initial_message: "Welcome to the interview..."
  max_questions: 10
  max_retries: 2
  initial_context: {}

logging:
  save_to_file: true
  output_dir: "logs"
  filename_template: "session_{timestamp}.log"

report:
  save_to_file: true
  output_dir: "reports"
  filename_template: "report_{timestamp}.txt"

```
### 📄 Example Configurations

Refer to the following examples for creating your own configuration:

- [Math Problem Solving](https://github.com/interview-eval/interview-eval/blob/main/examples/configs/math_problem_solving.yaml)
- [Café Part-Time Job Scenario](https://github.com/interview-eval/interview-eval/blob/main/examples/configs/cafe_parttime.yaml)

## 🔑 Guideline for Customizing the YAML File

This guide explains how to customize the YAML file based on your needs to create and configure an effective interview session between an interviewer and an interviewee.

### Table of Contents for Customization
- [Interview Type](#1-interview-type)
- [Interviewer Configuration](#2-interviewer-configuration)
    - [Basic Settings](#basic-settings)
    - [Instructions](#instructions)
    - [hint_prompt_template](#hint-strategy)
    - [strategy](#questioning-strategy-for-follow-up-questions)
    - [Seed Question](#seed-question)
    - [Rubric](#grading-rubric)
- [Interviewee Configuration](#3-interviewee-configuration)
    - [Basic Settings](#basic-settings-1)
    - [Instructions](#instructions-1)
- [Session Configuration](#4-session-configuration)
- [Logging Configuration](#5-logging-configuration)
- [Interview Report Configuration](#6-reporting-configuration)
- [Customization Tips](#customization-tips)

---

### **1. Interview Type**
Define the type of interview:
```yaml
interview_type: <type>
```

---

### **2. Interviewer Configuration**
The `interviewer` section customizes the behavior and attributes of the interviewer.

#### **Basic Settings**
```yaml
interviewer:
  name: "<Interviewer Name>"
  model: "<Interviewer AI Model>"
  client:
    api_key: ${<API_KEY_VARIABLE>}
```
- **`name`**: Provide a name for the interviewer (e.g., "Teacher").
- **`model`**: Specify the AI model to use (e.g., `gpt-4o-mini`).
- **`api_key`**: Add the API key environment variable. (e.g., `${OPENAI_API_KEY}`).

#### **Instructions**
Define the behavior and goals of the interviewer:
```yaml
  instructions: |
    <Interviewer instructions here>
```
- Example: "You are a science interviewer assessing high school knowledge. Topics to cover: Biology, Physics."

#### **Hint Strategy**

This is the prompt used when the interviewer provides hints (feedback) to the interviewee. Customize how the interviewer provides hints:
```yaml
  hint_prompt_template: |
    "<Hint strategy description>"
```
If not specified, it will default to the following:
- Default: "Given the following, you have to give a hint to the interviewee to help them answer the question correctly. \nIf the {interviewee_name} makes repeated mistakes, give more hints to fix the mistake.\n"

#### **Questioning Strategy For Follow-Up Questions**
This is the instruction used when the interviewer provides follow-up questions to the interviewee.

Define the approach to questioning:
```yaml
  strategy:
    max_questions: <Number>
    policy:
      - "<Questioning rule 1>"
      - "<Questioning rule 2>"
    follow_up_rules:
      - "<Follow-up rule 1>"
      - "<Follow-up rule 2>"
```
- **`max_questions`**: Set the maximum number of questions allowed.
- **`policy`**: Define the overall questioning flow (e.g., increasing difficulty, no duplicates).
- **`follow_up_rules`**: Specify how to probe deeper or handle incomplete answers.

#### **Seed Question**

Provide the initial question to kickstart the interview:

```yaml
  seed_question: "<First question>"
```

- If you are not using the existing benchmark dataset and prefer to define your own scenario (e.g., a café interview scenario), you can set your custom seed question here.
- If you are using a benchmark dataset, the seed question can be dynamically assigned as follows:

```python
interviewer = Interviewer(config=config_data, name="Interviewer")
interviewer.seed_question = question['question']
interviewer.seed_question_answer = question['solution']
```

#### **Grading Rubric**
Specify the grading criteria:
```yaml
  rubric: |
    <Grading criteria>
```
- Example: "Score from 0-10 based on problem-solving accuracy and explanation depth."

---

### **3. Interviewee Configuration**
The `interviewee` section defines the simulated student or participant.

#### **Basic Settings**
```yaml
interviewee:
  name: "<Interviewee Name>"
  model: "<Interviewee AI Model>"
  client:
    api_key: ${<API_KEY_VARIABLE>}
```
- **`name`**: Name of the participant (e.g., "Student").
- **`model`**: Specify the AI model (e.g., `openai/gpt-4o-mini-2024-07-18`).

#### **Instructions**
Define the participant’s role, strengths, and challenges:
```yaml
  instructions: |
    <Interviewee instructions here>
```
- Example: "You are a high school student who excels in Geometry but struggles with Algebra."

---

### **4. Session Configuration**
Control session parameters, such as retries and initial messages:
```yaml
session:
  max_questions: <Number>
  max_retries: <Number>
  initial_message: "<Message>"
  initial_context:
    interview_complete: <true/false>
    current_topic: "<Topic>"
    questions_asked: <Number>
    assessment_notes: []
```
- **`max_questions`**: Limit the session length.
- **`max_retries`**: Set how many retries are allowed.
- **`initial_message`**: Customize the opening message.
- **`initial_context`**: Define the starting context, such as the topic and initial notes.

---

### **5. Logging Configuration**
Enable or disable logging and customize log file details:
```yaml
logging:
  save_to_file: <true/false>
  output_dir: "<Directory>"
  filename_template: "<Filename format>"
```
- **`save_to_file`**: Set to `true` to save logs.
- **`output_dir`**: Define the directory for logs.
- **`filename_template`**: Use placeholders like `{timestamp}` for dynamic filenames.

---

### **6. Interview Report Configuration**
Control Interview Report Saving options for the session:
```yaml
report:
  save_to_file: <true/false>
  output_dir: "<Directory>"
  filename_template: "<Filename format>"
```
- Similar to the logging configuration, but for reports.

---

### **Customization Tips**
- **Focus on Roles:** Clearly define interviewer and interviewee roles for clarity in behavior.
- **Adapt Strategies:** Tailor hint and questioning strategies to align with the interview's goals.
- **Contextual Seed Questions:** Use a relevant seed question to set the tone.
- **Test Configuration:** Validate settings in a test environment to ensure smooth performance.
- **Dynamic Variables:** Leverage placeholders (e.g., `${OPENAI_API_KEY}`, `{timestamp}`) for flexibility.

## 🔄 Question Decontamination

For users conducting benchmark-based interview (like GSM8K, MMLU, etc.), `interview-eval` provides functions to prevent test set contamination through three transformation strategies:

```python
from interview_eval import decontaminate_question

# Choose from three decontamination methods
question = decontaminate_question(
    question="What is 15% of 200?",
    reference_answer="30",
    method="modifying"  # or "unclarifying" or "paraphrasing"
)
```

1. **Unclarifying** (`method="unclarifying"`)
   - Removes key information while maintaining grammar
   - Forces interviewee to ask clarifying questions
   - Evaluates information-gathering skills

2. **Paraphrasing** (`method="paraphrasing"`)
   - Preserves exact meaning with different wording
   - Changes sentence structure
   - Maintains problem complexity

3. **Modifying** (`method="modifying"`)
   - Creates new but related questions
   - Keeps similar domain and difficulty
   - Tests same knowledge areas


Batch processing of questions is also supported:

```python
from interview_eval import batch_decontaminate

questions = [
    {"question": "Q1...", "reference_answer": "A1..."},
    {"question": "Q2...", "reference_answer": "A2..."}
]

decontaminated = batch_decontaminate(
    questions,
    method="modifying",
    model="gpt-4"
)
```
