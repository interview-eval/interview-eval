# interview-swarm

Interview Process implemented in Swarm. Will be integrated with interview-eval in the future.

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
- [ ] Add documentation for the code
- [ ] Support interview_type: "base", "adaptive"
- [ ] Fix the organization for cli support
- [ ] Add tests
- [ ] Hide logging inside the Runner
- [ ] Add support for seed questions
- [ ] Release to PyPI