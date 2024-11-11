from swarm import Swarm, Agent, Result
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


class Interviewer(Agent):
    def __init__(
        self,
        name: str = "Math Interviewer",
        difficulty: str = "intermediate",  # "basic", "intermediate", or "advanced"
        topics: List[str] = None,
    ):
        if topics is None:
            topics = ["Algebra", "Geometry", "Basic Calculus"]

        def conclude_interview(score: int, comments: str) -> Result:
            """
            Conclude the interview with final score and comments.

            Args:
                score: Math assessment score from 1-10
                comments: Detailed comments about the student's understanding
            """
            return Result(
                value=f"Interview concluded. Score: {score}/10\nComments: {comments}",
                context_variables={
                    "interview_complete": True,
                    "score": score,
                    "comments": comments,
                },
            )

        instructions = f"""You are a math interviewer assessing student knowledge at the {difficulty} level.
        
        Topics to cover: {', '.join(topics)}
        
        Interview process:
        1. Start with simple warm-up questions
        2. Progress to more complex problems within the chosen topics
        3. Ask the student to explain their thinking process
        4. Provide hints if the student is stuck
        5. Use conclude_interview() when you've assessed their understanding
        
        Guidelines:
        - Ask one question at a time
        - Start with easier questions and gradually increase difficulty
        - Ask students to explain their reasoning
        - Be encouraging but objective in your assessment
        - Give students time to think
        - Correct any misconceptions politely
        
        Sample questions for {difficulty} level:
        - Algebra: Solve quadratic equations, simplify expressions
        - Geometry: Calculate areas, understand properties of shapes
        - Basic Calculus: Derivatives, simple integrals, rate of change problems
        """

        super().__init__(
            name=name, instructions=instructions, functions=[conclude_interview]
        )


class Interviewee(Agent):
    def __init__(
        self,
        name: str = "Student",
        math_level: str = "high school",
        strong_topics: List[str] = None,
        weak_topics: List[str] = None,
    ):
        if strong_topics is None:
            strong_topics = ["Algebra"]
        if weak_topics is None:
            weak_topics = ["Calculus"]

        instructions = f"""You are a math student at the {math_level} level.
        
        Your background:
        - Strong topics: {', '.join(strong_topics)}
        - Topics you find challenging: {', '.join(weak_topics)}
        
        Guidelines:
        - Show your work and explain your thinking process
        - Ask for clarification if a question is unclear
        - Be honest if you don't understand something
        - Take your time to answer thoughtfully
        - Use mathematical terminology appropriately
        - Express confidence in topics you know well
        - Show willingness to learn from mistakes
        """

        super().__init__(name=name, instructions=instructions)


def run_math_interview():
    client = Swarm()

    interviewer = Interviewer(
        name="User",
        difficulty="intermediate",
        topics=["Algebra", "Geometry", "Trigonometry"],
    )

    student = Interviewee(
        name="System",
        math_level="high school",
        strong_topics=["Algebra", "Geometry"],
        weak_topics=["Trigonometry"],
    )

    # Start interview
    messages = [
        {
            "role": "user",
            "content": "Hello! Let's begin with some math problems. Are you ready to start?",
        }
    ]

    # Run interview simulation
    response = client.run(
        agent=student,
        messages=messages,
        context_variables={
            "interview_complete": False,
            "current_topic": "warm-up",
            "questions_asked": 0,
        },
    )

    # Continue interview until concluded
    while not response.context_variables.get("interview_complete", False):
        # Switch between interviewer and student
        current_agent = interviewer if response.agent == student else student

        # Add the last message to the conversation
        messages = response.messages + [
            {"role": "user", "content": response.messages[-1]["content"]}
        ]

        # Update context with question count
        if current_agent == interviewer:
            response.context_variables["questions_asked"] = (
                response.context_variables.get("questions_asked", 0) + 1
            )

        # Run the next turn of the conversation
        response = client.run(
            agent=current_agent,
            messages=messages,
            context_variables=response.context_variables,
        )

        # Print the ongoing conversation
        print(f"\n{response.agent.name}: {response.messages[-1]['content']}\n")

        # If interview is complete, print final results
        if response.context_variables.get("interview_complete"):
            print("\n=== Math Assessment Results ===")
            print(f"Score: {response.context_variables['score']}/10")
            print(f"Comments: {response.context_variables['comments']}")


if __name__ == "__main__":
    run_math_interview()
