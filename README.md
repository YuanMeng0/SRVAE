# SRVAE: A Semantic Network based Deep Residual Variational Auto-Encoder for Image Compression
## Install

**Requirements**:

- Python
- PyTorch >= 1.9 : https://pytorch.org/get-started/locally
- tqdm : `conda install tqdm`
- CompressAI : https://github.com/InterDigitalInc/CompressAI
- **timm >= 0.8.0** : https://github.com/huggingface/pytorch-image-models

### Dataset

**COCO**

1. Download the COCO dataset "2017 Train images [118K/18GB]" from https://cocodataset.org/#download
2. Unzip the images anywhere, e.g., at `/path/to/datasets/coco/train2017`
3. Edit `srvae/lvae/paths.py` such that

```
known_datasets['coco-train2017'] = '/path/to/datasets/coco/train2017'
```

**Kodak** ([link](http://r0k.us/graphics/kodak)),
**Tecnick TESTIMAGES** ([link](https://testimages.org/)),
and **CLIC** ([link](http://compression.cc/))

