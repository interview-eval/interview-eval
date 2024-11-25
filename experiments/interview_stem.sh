
python interview_stem.py \
--model_moderator gpt-4o \
--model_evaluator gpt-4o \
--model_evaluatee gpt-3.5-turbo \
--names 0 \
--state_threshold 3 \
--start_query_index 0 \
--init_action modifying \
--task stem \
--output_path ./outputs/1023_stem/gpt35_new.csv &


python interview_stem.py \
--model_moderator gpt-4o \
--model_evaluator gpt-4o \
--model_evaluatee gpt-4o \
--names 0 \
--state_threshold 3 \
--start_query_index 0 \
--init_action modifying \
--task stem \
--output_path ./outputs/1023_stem/gpt4_new.csv  &

