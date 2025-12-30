import unittest
from unittest.mock import patch, MagicMock
import os
from screen_recorder.recorder.merger import check_ffmpeg, merge_audio_video

class TestMerger(unittest.TestCase):
    @patch('subprocess.run')
    def test_check_ffmpeg(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(check_ffmpeg())
        
        mock_run.side_effect = FileNotFoundError
        self.assertFalse(check_ffmpeg())
        
    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_merge_audio_video(self, mock_remove, mock_exists, mock_run):
        # Setup
        mock_exists.return_value = True # Files exist
        mock_run.return_value.returncode = 0 # Success
        
        # Run
        result = merge_audio_video("vid.avi", "aud.wav", "out.mp4", keep_temp=False)
        
        # Verify
        self.assertTrue(result)
        # Verify command args
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "ffmpeg")
        self.assertIn("-c:v", args)
        self.assertIn("copy", args)
        
        # Verify cleanup
        self.assertEqual(mock_remove.call_count, 2) # Video and Audio removed

if __name__ == '__main__':
    unittest.main()
