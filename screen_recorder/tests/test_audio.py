import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Pre-emptive mocking of sounddevice before any import that might use it
mock_sd = MagicMock()
sys.modules['sounddevice'] = mock_sd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from recorder.audio_capture import AudioRecorder

class TestAudioRecorder(unittest.TestCase):
    @patch('wave.open')
    def test_audio_recording_lifecycle(self, mock_wave_open):
        # Setup mocks
        mock_sd.query_devices.return_value = [{'name': 'Mock Device', 'index': 0}]
        
        # Mock InputStream context manager
        mock_stream_instance = MagicMock()
        mock_sd.InputStream.return_value.__enter__.return_value = mock_stream_instance
        
        # Because we mocked sys.modules, AudioRecorder.sd is our mock_sd
        # We need to ensure HAS_SOUNDDEVICE is True in the module if we want to test the "happy path"
        # Since we mocked it before import, the import inside AudioRecorder should have succeeded 
        # (it returns the mock).
        
        # Initialize recorder
        rec = AudioRecorder(filename="test_audio.wav")
        
        # Start
        rec.start()
        self.assertTrue(rec.recording)
        
        # Stop
        rec.stop()
        self.assertFalse(rec.recording)
        
        # Verify calls
        mock_sd.InputStream.assert_called()

if __name__ == '__main__':
    unittest.main()
