# CUDA_VISIBLE_DEVICES=4,5 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python src/models.py \
# --model zephyr-stem-test

# CUDA_VISIBLE_DEVICES=4,5 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python src/models.py \
# --model zephyr-stem-test-half

CUDA_VISIBLE_DEVICES=4,5 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python src/models.py \
--model zephyr-stem-train

