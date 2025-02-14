import torch
from torch.hub import load_state_dict_from_url

from lvae.models.registry import register_model
import lvae.models.common as common
import lvae.models.srvae.model as srvae


@register_model
def srvae_base(lmb_range=(16,2048), pretrained=False):
    cfg = dict()

    # mean and std computed on imagenet
    cfg['im_shift'] = -0.4546259594901961
    cfg['im_scale'] = 3.67572653978347
    # maximum downsampling factor
    cfg['max_stride'] = 64
    # images used during training for logging
    cfg['log_images'] = ['collie64.png', 'gun128.png', 'motor256.png']

    # variable-rate
    cfg['lmb_range'] = (float(lmb_range[0]), float(lmb_range[1]))
    cfg['lmb_embed_dim'] = (256, 256)
    cfg['sin_period'] = 64
    # _emb_dim = cfg['lmb_embed_dim'][1]

    # model configuration
    ch = 128
    enc_dims = [192, ch*3, ch*4, ch*4, ch*4]

    res_block = common.ConvNeXtBlockAdaLN
    res_block.default_embedding_dim = cfg['lmb_embed_dim'][1]

    im_channels = 3
    cfg['enc_blocks'] = [
        # 64x64
        common.patch_downsample(im_channels, enc_dims[0], rate=4),
        # 16x16
        *[res_block(enc_dims[0], kernel_size=7) for _ in range(6)],
        res_block(enc_dims[0]),
        common.patch_downsample(enc_dims[0], enc_dims[1]),
        # 8x8
        *[res_block(enc_dims[1], kernel_size=7) for _ in range(6)],
        common.SetKey('enc_s8'),
        res_block(enc_dims[1]),
        common.patch_downsample(enc_dims[1], enc_dims[2]),
        # 4x4
        *[res_block(enc_dims[2], kernel_size=5) for _ in range(6)],
        common.SetKey('enc_s16'),
        res_block(enc_dims[2]),
        common.patch_downsample(enc_dims[2], enc_dims[3]),
        # 2x2
        *[res_block(enc_dims[3], kernel_size=3) for _ in range(4)],
        common.SetKey('enc_s32'),
        res_block(enc_dims[3]),
        common.patch_downsample(enc_dims[3], enc_dims[4]),
        # 1x1
        *[res_block(enc_dims[4], kernel_size=1) for _ in range(4)],
        common.SetKey('enc_s64'),
    ]

    dec_dims = [ch*4, ch*4, ch*3, ch*2, ch*1]
    z_dims = [32, 32, 96, 8]
    cfg['dec_blocks'] = [
        # 1x1
        *[srvae.VRLVBlockBase(dec_dims[0], z_dims[0], enc_key='enc_s64', enc_width=enc_dims[-1], kernel_size=1, mlp_ratio=4) for _ in range(1)],
        res_block(dec_dims[0], kernel_size=1, mlp_ratio=4),
        common.patch_upsample(dec_dims[0], dec_dims[1], rate=2),
        # 2x2
        res_block(dec_dims[1], kernel_size=3, mlp_ratio=3),
        *[srvae.VRLVBlockBase(dec_dims[1], z_dims[1], enc_key='enc_s32', enc_width=enc_dims[-2], kernel_size=3, mlp_ratio=3) for _ in range(2)],
        res_block(dec_dims[1], kernel_size=3, mlp_ratio=3),
        common.patch_upsample(dec_dims[1], dec_dims[2], rate=2),
        # 4x4
        res_block(dec_dims[2], kernel_size=5, mlp_ratio=2),
        *[srvae.VRLVBlockBase(dec_dims[2], z_dims[2], enc_key='enc_s16', enc_width=enc_dims[-3], kernel_size=5, mlp_ratio=2) for _ in range(3)],
        res_block(dec_dims[2], kernel_size=5, mlp_ratio=2),
        common.patch_upsample(dec_dims[2], dec_dims[3], rate=2),
        # 8x8
        res_block(dec_dims[3], kernel_size=7, mlp_ratio=1.75),
        *[srvae.VRLVBlockBase(dec_dims[3], z_dims[3], enc_key='enc_s8', enc_width=enc_dims[-4], kernel_size=7, mlp_ratio=1.75) for _ in range(3)],
        common.CompresionStopFlag(), # no need to execute remaining blocks when compressing
        res_block(dec_dims[3], kernel_size=7, mlp_ratio=1.75),
        common.patch_upsample(dec_dims[3], dec_dims[4], rate=2),
        # 16x16
        *[res_block(dec_dims[4], kernel_size=7, mlp_ratio=1.5) for _ in range(8)],
        common.patch_upsample(dec_dims[4], im_channels, rate=4)
    ]

    model = srvae.VariableRateLossyVAE(cfg)

    if pretrained is True:
        msd = load_state_dict_from_url(url)['model']
        model.load_state_dict(msd)
    elif pretrained: # str or Path
        msd = torch.load(pretrained)['model']
        model.load_state_dict(msd)
    return model
