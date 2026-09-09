import logging
import threading
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger("sentinel.vision.detection.model_manager")


class YOLOModelManager:
    """
    Thread-safe singleton model manager for Ultralytics YOLO models.
    Loads and caches the model instance in memory to avoid per-frame reloading.
    """

    _instance: Optional["YOLOModelManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "YOLOModelManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(YOLOModelManager, cls).__new__(cls)
                cls._instance._model = None
                cls._instance._model_name = None
                cls._instance._device = None
                cls._instance._load_error = None
            return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def get_model(self, model_name: Optional[str] = None, device: Optional[str] = None) -> Any:
        """
        Retrieve the cached model instance, loading it on-demand if necessary.

        Args:
            model_name: Optional model identifier (defaults to settings.YOLO_MODEL)
            device: Optional target device (defaults to settings.YOLO_DEVICE)

        Returns:
            Ultralytics YOLO model instance.

        Raises:
            RuntimeError: If model initialization or weight loading fails.
        """
        target_model = model_name or settings.YOLO_MODEL
        target_device = device or settings.YOLO_DEVICE

        with self._lock:
            # Return cached instance if already loaded with matching configuration
            if self._model is not None and self._model_name == target_model:
                return self._model

            # Attempt to initialize and load model
            return self._load_model(target_model, target_device)

    def _load_model(self, model_name: str, target_device: str) -> Any:
        logger.info(f"Initializing YOLO detection model: '{model_name}' (device: {target_device})...")

        try:
            from ultralytics import YOLO
        except ImportError as e:
            msg = "Ultralytics package is not installed. Please run: pip install ultralytics"
            logger.error(msg)
            self._load_error = msg
            raise RuntimeError(msg) from e

        # Resolve device
        resolved_device = "cpu"
        if target_device.lower() in ("cuda", "auto"):
            try:
                import torch
                if torch.cuda.is_available() and target_device.lower() != "cpu":
                    resolved_device = "cuda"
                    logger.info(f"CUDA acceleration available: {torch.cuda.get_device_name(0)}")
                else:
                    logger.info("CUDA not available or CPU requested; falling back to CPU.")
            except ImportError:
                logger.info("Torch not directly queryable for CUDA; using CPU.")

        try:
            # Instantiate model (weights will download automatically on first run if not present)
            model = YOLO(model_name)

            self._model = model
            self._model_name = model_name
            self._device = resolved_device
            self._load_error = None

            logger.info(f"YOLO model '{model_name}' successfully loaded and cached on {resolved_device}.")
            return self._model

        except Exception as e:
            self._load_error = str(e)
            logger.exception(f"Failed to load YOLO model '{model_name}': {e}")
            raise RuntimeError(f"Unable to initialize YOLO detection model '{model_name}': {e}") from e

    def clear_cache(self) -> None:
        """Release cached model from memory."""
        with self._lock:
            self._model = None
            self._model_name = None
            self._device = None
            self._load_error = None
            logger.info("YOLO model cache cleared.")


_manager = YOLOModelManager()


def get_model_manager() -> YOLOModelManager:
    """Access the global YOLOModelManager singleton."""
    return _manager
