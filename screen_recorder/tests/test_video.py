import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from recorder.video_capture import VideoRecorder

class TestVideoRecorder(unittest.TestCase):
    @patch('mss.mss')
    @patch('cv2.VideoWriter')
    def test_video_recording_lifecycle(self, mock_video_writer, mock_mss):
        # Setup mocks
        mock_sct = MagicMock()
        mock_mss.return_value = mock_sct
        
        # Mock monitor data
        mock_sct.monitors = [
            {"top": 0, "left": 0, "width": 1920, "height": 1080}, # index 0 (all)
            {"top": 0, "left": 0, "width": 1920, "height": 1080}  # index 1 (primary)
        ]
        
        # Mock grab result (need a valid numpy array structure)
        # MSS grab returns an object that can be converted to array
        mock_img = MagicMock()
        # when np.array(mock_img) is called, we need it to work. 
        # But VideoRecorder calls np.array(img).
        # Let's mock the grab return to be a real numpy array or something compatible.
        dummy_frame = np.zeros((1080, 1920, 4), dtype=np.uint8)
        mock_sct.grab.return_value = dummy_frame

        # Initialize recorder
        rec = VideoRecorder(filename="test_output.avi", fps=30)
        
        # Start recording
        rec.start()
        self.assertTrue(rec.recording)
        
        # Wait a bit
        time.sleep(0.5)
        
        # Pause
        rec.pause()
        self.assertTrue(rec.paused)
        
        # Resume
        rec.resume()
        self.assertFalse(rec.paused)
        
        # Stop
        rec.stop()
        self.assertFalse(rec.recording)
        
        # Verify calls
        mock_sct.grab.assert_called()
        mock_video_writer.return_value.write.assert_called()
        mock_video_writer.return_value.release.assert_called()

if __name__ == '__main__':
    unittest.main()
