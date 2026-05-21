from __future__ import annotations

from benchmark.config import DISPLAY_HEIGHT, DISPLAY_WIDTH, MODEL_CONFIG, ModelCfg


def computer_tool(cfg: ModelCfg) -> dict:
    return {
        "type": cfg.tool_version,
        "name": "computer",
        "display_width_px": DISPLAY_WIDTH,
        "display_height_px": DISPLAY_HEIGHT,
        "display_number": 1,
    }


def tools_for(model_id: str) -> list[dict]:
    return [computer_tool(MODEL_CONFIG[model_id])]
