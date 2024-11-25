
CUDA_VISIBLE_DEVICES=1,0 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python interview_math.py \
--model_moderator gpt-4o \
--model_evaluator gpt-4o \
--model_evaluatee llama-3.1-70b \
--names 0 \
--state_threshold 3 \
--start_query_index 0 \
--init_action unclarifying \
--output_path outputs/1016_llm/math_llama31.csv &



CUDA_VISIBLE_DEVICES=1,0 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python interview_math.py \
--model_moderator gpt-4o \
--model_evaluator gpt-4o \
--model_evaluatee gpt-3.5-turbo \
--names 0 \
--state_threshold 3 \
--start_query_index 0 \
--init_action unclarifying \
--output_path outputs/1016_llm/math_gpt35.csv 

# CUDA_VISIBLE_DEVICES=1,0 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python interview_math.py \
# --model_moderator gpt-4o \
# --model_evaluator gpt-4o \
# --model_evaluatee gpt-4o \
# --names 0 \
# --state_threshold 3 \
# --start_query_index 0 \
# --init_action unclarifying \
# --output_path outputs/1016_llm/math_gpt4.csv 

# CUDA_VISIBLE_DEVICES=1,0 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python interview_math.py \
# --model_moderator gpt-4o \
# --model_evaluator gpt-4o \
# --model_evaluatee olmoe-math-train-test \
# --names 0 \
# --state_threshold 3 \
# --start_query_index 0 \
# --init_action unclarifying \
# --output_path outputs/1016_llm/math_train_test_par_0925_base.csv
