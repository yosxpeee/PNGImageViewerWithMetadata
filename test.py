import os


text = 'Steps: 25, Sampler: DPM++ 2M, Schedule type: Karras, CFG scale: 7, Seed: 3158555784, Size: 572x1024, Model hash: d64c08ec07, Model: divingIllustriousSemi_v10, Denoising strength: 0.7, Clip skip: 2, Hires Module 1: Use same choices, Hires CFG Scale: 7, Hires upscale: 2, Hires upscaler: Latent, Lora hashes: "NamieAmuro_for_Diving-Illustrious_Semi-Real_v1: 4a806b3db7ab, eyepatch-bikini-illustriousxl-lora-nochekaiser: bb10e9ffa412", Version: f2.0.1v1.10.1-previous-665-gae278f79, Module 1: sdxlVAE_sdxlVAE'


if "divingIllustriousSemi_v10" in text:
    print("含む")
else:
    print("含まない")