# LLM-as-an-Interviewer
This is the official GitHub repository for [LLM-AS-AN-INTERVIEWER: Beyond Static Testing Through Dynamic LLM Evaluation](https://arxiv.org/abs/2412.10424).

LLM-as-an-Interviewer is an evaluation framework that assesses the capabilities of LLMs through an interview-style process. In this approach, the LLM acting as the interviewer evaluates other LLMs by providing feedback and asking follow-up questions, enabling a more comprehensive assessment of their capabilities.

Our framework includes a flexible pipeline that can be easily adapted to various tasks by incorporating a customized evaluation rubric.

## 🚀 Quick Start
- Git Clone
- Install requirements
```
"openai>=1.55.2",
"python-dotenv>=1.0.1",
"pyyaml>=6.0.2",
"rich>=13.9.4",
"click"
```

- Setup API key in .env file
```
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
```


- ***Note:*** To test local models, you can use [vLLM serve](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html?ref=blog.mozilla.ai) to launch the OpenAI compatible server.


- Run the following command to start the interview
```bash
python libs/interview_eval/main.py --config examples/configs/math_problem_solving.yaml
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

## Basic Usage

- All you need is the below code snippet and your customized `config.yaml` file!

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