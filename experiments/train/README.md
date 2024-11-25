##  Instructions for Training

```bash
cd /train

# clone axolotl and setup the environment

conda activate axolotl

accelerate launch -m axolotl.cli.train config.yaml
```