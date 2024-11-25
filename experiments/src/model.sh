CUDA_VISIBLE_DEVICES=3,4 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python src/models.py \
--model olmoe-stem-train

# CUDA_VISIBLE_DEVICES=4,5 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python src/models.py \
# --model olmoe-stem-test-half

# CUDA_VISIBLE_DEVICES=4,5 HF_HOME=/mnt/nas2/eval-paradox/model/checkpoints python src/models.py \
# --model olmoe-stem-train

