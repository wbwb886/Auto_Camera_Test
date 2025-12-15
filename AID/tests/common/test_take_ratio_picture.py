import pytest
import time,logging
from utils.uiautomator_helper import UIAutomatorHelper
from utils.opencv_utils import OpenCVUtils
from utils.report_utils import SimpleReport
from config.device_config import DEVICE_ID, OUTPUT_PATH

logger = logging.getLogger(__name__)
loops = 1
RATIO_LEVELS = ["1:1", "3:4", "9:16", "full"]

@pytest.fixture
def setup_device():
    ui = UIAutomatorHelper(DEVICE_ID)
    yield ui
    ui.back_to_home()

def test_take_ratio_picture(setup_device):
    """拍照并校验"""
    report = SimpleReport()
    case_name = "test_take_ratio_picture"
    ui = setup_device
    ui.open_camera()
    for ratio in RATIO_LEVELS:
        ui.set_ratio(ratio)
        ui.take_picture(loops)
    ui.set_ratio()

    # 自动拉取照片
    local_photos = ui.pull_all_photo()
    logger.info(f"已拉取照片: {local_photos}")
    assert len(local_photos) > 0

    # report
    result, comments = OpenCVUtils.validate_and_collect(OUTPUT_PATH, check_3a=False, check_abnormal=True)
    report.add_result(case_name, loops, result, comments)
    if result == "FAIL":
        raise AssertionError(comments)