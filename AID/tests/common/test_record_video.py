import pytest
import time,logging
from utils.uiautomator_helper import UIAutomatorHelper
from utils.opencv_utils import OpenCVUtils
from utils.report_utils import SimpleReport
from config.device_config import DEVICE_ID, OUTPUT_PATH

logger = logging.getLogger(__name__)
loops = 1

@pytest.fixture
def setup_device():
    ui = UIAutomatorHelper(DEVICE_ID)
    yield ui
    ui.back_to_home()

def test_record_video(setup_device):
    """录制并校验"""
    report = SimpleReport()
    case_name = "test_record_video"
    ui = setup_device
    ui.open_camera()
    ui.switch_video_mode()
    ui.start_recording()
    time.sleep(5)
    ui.stop_recording()

    # 自动拉取视频
    local_photos = ui.pull_all_video()
    logger.info(f"已拉取视频: {local_photos}")
    assert len(local_photos) > 0

    # report
    result, comments = OpenCVUtils.validate_and_collect(OUTPUT_PATH, check_video=True)
    report.add_result(case_name, loops, result, comments)
    if result == "FAIL":
        raise AssertionError(comments)