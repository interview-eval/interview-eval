python interview_test_math.py \
--model_moderator math-interviewer \
--model_evaluator math-interviewer \
--model_evaluatee interviewee \
--names 0 \
--state_threshold 3 \
--start_query_index 0 \
--followup_flag 0 \
--init_action unclarifying \
--output_path testcase_1.csv

python interview_test_math.py \
--model_moderator math-interviewer \
--model_evaluator math-interviewer \
--model_evaluatee interviewee \
--names 0 \
--state_threshold 1 \
--start_query_index 0 \
--followup_flag 0 \
--init_action unclarifying \
--output_path testcase_2.csv
