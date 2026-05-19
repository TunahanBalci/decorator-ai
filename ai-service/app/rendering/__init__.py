"""Rendering package — pluggable furniture renderers.

Supported render methods:
- ``overlay``: Sprint 2 perspective-aware PNG overlay (default, no GPU).
- ``mock_inpaint``: Simulates SDXL pipeline (mask + prompt + debug) without AI.
- ``sdxl_inpaint``: Placeholder for real SDXL/ControlNet (requires GPU deps).
- ``external_ai``: Placeholder for external API services (Replicate, Stability, etc.).

Use :func:`app.rendering.factory.get_renderer` to obtain a renderer instance.
"""
