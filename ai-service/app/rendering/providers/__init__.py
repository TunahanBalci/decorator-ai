"""Rendering providers — pluggable AI inpainting backends.

Providers implement the actual image generation call (local GPU, cloud API,
or mock).  The :class:`ExternalAIInpaintRenderer` selects a provider at
runtime based on configuration.

Supported providers:
- ``mock``: Saves request payload, returns overlay (no API key needed)
- ``replicate``: Replicate API (future)
- ``huggingface``: Hugging Face Inference API (future)
- ``stability``: Stability AI API (future)
"""
