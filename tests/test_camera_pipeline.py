from src.gui.providers.camera_pipeline import CameraPipeline


def test_camera_pipeline_constructs_and_exposes_providers():
    # Construction alone must never open a real camera -- only .start() does,
    # via the worker thread's `started` signal -- so this test never calls it.
    pipeline = CameraPipeline()

    assert pipeline.hand_provider is not None
    assert pipeline.calibration_provider is not None
