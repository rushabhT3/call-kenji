"""Load any ONNX backchannel model from a path in config; no code change to swap models.

Model contract:
    input  0: string tensor, shape [1, N], one spoken character per element
              (whitespace and punctuation removed; Japanese is never split on spaces)
    output 0: float tensor whose last element is P(real interruption) in [0, 1]
"""

from pathlib import Path

import numpy as np
import onnxruntime

from kenji.domain.text import spoken_characters
from kenji.domain.turn import TurnDecision, TurnPolicy, decide


class OnnxBackchannelClassifier:
    def __init__(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(f"backchannel model not found: {model_path}")
        self._session = onnxruntime.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )
        self._input_name = self._session.get_inputs()[0].name

    def classify(self, utterance: str, policy: TurnPolicy) -> TurnDecision:
        characters = list(spoken_characters(utterance)) or [""]
        outputs = self._session.run(None, {self._input_name: np.array([characters], dtype=object)})
        probability = float(np.asarray(outputs[0]).reshape(-1)[-1])
        return decide(utterance, min(1.0, max(0.0, probability)), policy)
