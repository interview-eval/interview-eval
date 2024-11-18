# stateDiagram-v2
#     [*] --> Initial
#     Initial --> Question
    
#     Question --> EvaluateResponse
    
#     EvaluateResponse --> DeepDive: Technical detail needed
#     EvaluateResponse --> Challenge: Clarification needed
#     EvaluateResponse --> NextTopic: Satisfactory answer
#     EvaluateResponse --> Conclude: Understanding complete

#     DeepDive --> Question
#     Challenge --> Question
#     NextTopic --> Question
    
#     Conclude --> [*]


# Define another state diagram agent for the adaptive interview
# The interview process will be adaptive based on the responses of the interviewee