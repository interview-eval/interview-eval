# interview-eval

An automated interview evaluation system that simulates technical interviews using AI agents. The system consists of an AI interviewer and interviewee, conducting structured conversations based on predefined rubrics and strategies.

## Quick Test (12.05)

- Intall requirements
```
"openai>=1.55.2",
"python-dotenv>=1.0.1",
"pyyaml>=6.0.2",
"rich>=13.9.4",
```

- Setup API key in .env file
  - Local models can be evaluated through VLLM serve
```
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```

```bash
python libs/interview-eval/main.py --config examples/math_problem_solving.yaml
```

## 📦 Installation

```bash
pip install interview-eval
```

## 🌟 Features

- AI-powered interviewer and interviewee agents
- Configurable interview parameters and evaluation rubrics
- Real-time conversation display with rich formatting
- Detailed scoring and feedback system
- Progress tracking and maximum question limits
- Customizable OpenAI client configuration

## 🚀 Quick Start

```python
from interview_eval import InterviewRunner, Interviewer, Interviewee
from interview_eval.utils import console, load_config, setup_logging
import logging
import yaml

# Load configuration
config = load_config("config.yaml")

# Setup logging and console
logger = setup_logging("interview.log", verbose=True)

# Initialize agents
interviewer = Interviewer(config)
interviewee = Interviewee(config)

# Create and run interview
runner = InterviewRunner(interviewer, interviewee, config, logger, console)
results = runner.run()
```

## ⚙️ Configuration

Create a YAML configuration file with the following structure:

```yaml
interviewer:
  name: "Technical Interviewer"
  instructions: "Your interview guidelines..."
  rubric: "Evaluation criteria..."
  strategy:
    key_areas: [...]
    scoring_criteria: [...]
  client:  # Optional OpenAI client configuration
    api_key: "your-api-key"

interviewee:
  name: "Candidate"
  instructions: "Interviewee behavior guidelines..."

session:
  initial_message: "Welcome to the interview..."
  max_questions: 10
  max_retries: 2
  initial_context: {}
```

## 🎯 Advanced Interview

### Custom Interview Flows

***Note: This feature is still under development and will be available in future releases.***

`interview-eval` lets you define custom interview flows as directed graphs, where each node represents an interview state (like asking questions or evaluating responses) and edges represent possible transitions between states. With this feature, you can create complex interview scenarios with branching logic, follow-up questions, and adaptive feedback based on the interviewee's responses.

Below is an example flow of interview, where the Interviewer evaluates the Interviewee's response and chooses to do one of the following actions: 
- Ask a follow-up question (Deep Dive)
- Move on to the next topic (Next Topic)
- Ask for clarification (Challenge)
- End the interview (Conclude)

![Interview Flow](assets/interview-flow.png)


### Question Decontamination

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


### Requirements & TODOs

- Modifying problem ✔️
  - Python function to modify the problem `modify_problem`
  - Supported strategies: `Unclarifying`, `Paraphrasing`, and `Modifying` (given seed question, create a new question)

- Feedback & Editing Loop
  - Proceed to next question if the response is graded as `Good`
  - 이전에 했던 feedback 주지 말기

- Followup Questions
  - Problem, Response, Feedback, Followup Question, Response, Feedback, Followup Question, ...

- Report Card
  - Per seed questions pool
  - Include information about the student's performance on each question that received different scores


- [ ] More strict loading of config.yaml (e.g. check if all required fields are present)
- [X] Add documentation for the code
- [ ] Support interview_type: "base", "adaptive"
- [ ] Fix the organization for cli support
- [ ] Add tests
- [ ] Hide logging inside the Runner
- [ ] Add support for seed questions
- [ ] Release to PyPI
