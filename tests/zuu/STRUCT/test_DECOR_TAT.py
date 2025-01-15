import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from zuu.STRUCT.DECOR.track_and_terminate import lifetime

def test_function_completes_before_timeout():
    @lifetime("1m")
    def quick_function():
        return "done"
    
    result = quick_function()
    assert result == "done"

def test_function_times_out():
    @lifetime("1s")
    def slow_function():
        time.sleep(2)
        return "done"
    
    result = slow_function()
    assert result is None

def test_window_termination():
    # Setup mock pygetwindow module
    mock_pygetwindow = MagicMock()
    mock_window = MagicMock()
    mock_window.title = "TestWindow"
    mock_window._hWnd = 12345
    mock_window.close = MagicMock()
    mock_pygetwindow.getAllWindows.return_value = [mock_window]
    
    # Create a patch for sys.modules
    mock_modules = {
        'pygetwindow': mock_pygetwindow,
        'pygetwindow.getAllWindows': mock_pygetwindow.getAllWindows
    }
    
    with patch.dict('sys.modules', mock_modules):
        # Use a very short timeout (100 milliseconds)
        @lifetime("0.1 seconds", globs=["Test*"], usePsutil=False, diffInit=False)
        def window_function():
            time.sleep(0.5)  # Sleep longer than timeout
            return "Done"
        
        # Run function and capture result
        result = window_function()
        
        # Debug assertions
        assert mock_pygetwindow.getAllWindows.called, "getAllWindows was not called"
        assert len(mock_pygetwindow.getAllWindows.return_value) == 1, "No windows returned"
        assert mock_pygetwindow.getAllWindows.return_value[0].title == "TestWindow", "Window title mismatch"
        
        # Verify window was closed
        mock_window.close.assert_called_once()
        
        # Verify function was terminated
        assert result is None, "Function should have been terminated"

@patch('psutil.Process')
def test_process_termination(mock_process):
    # Mock process objects
    mock_child = MagicMock()
    mock_child.name.return_value = "test_process"
    mock_child.cmdline.return_value = ["test", "command"]
    mock_child.pid = 54321
    mock_child.terminate = MagicMock()
    mock_child.wait = MagicMock()
    
    mock_process_instance = MagicMock()
    mock_process_instance.children.return_value = [mock_child]
    mock_process.return_value = mock_process_instance
    
    @lifetime("0.1 seconds", globs=["test*"], usePygetwindow=False, diffInit=False)
    def process_function():
        time.sleep(0.5)
        return "Done"
    
    result = process_function()
    
    # Debug assertions
    assert mock_process.called, "Process constructor not called"
    assert mock_process_instance.children.called, "children() not called"
    assert mock_child.name.called, "name() not called"
    assert mock_child.cmdline.called, "cmdline() not called"
    
    # Verify process was terminated
    mock_child.terminate.assert_called_once()
    mock_child.wait.assert_called_once_with(timeout=3)
    
    # Verify function was terminated
    assert result is None, "Function should have been terminated"

def test_exception_propagation():
    @lifetime("1m")
    def error_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        error_function()

def test_diffinit_filtering():
    @patch('pygetwindow.getAllWindows')
    @patch('psutil.Process')
    def run_test(mock_process, mock_get_windows):
        # Mock initial windows
        initial_window = MagicMock()
        initial_window.title = "Initial Window"
        initial_window._hWnd = 11111
        
        # Mock new window
        new_window = MagicMock()
        new_window.title = "Test Window"
        new_window._hWnd = 22222
        
        # Setup window mocking
        mock_get_windows.side_effect = [
            [initial_window],  # Initial state
            [initial_window, new_window]  # During termination
        ]
        
        @lifetime("1s", globs=["Test*"], diffInit=True)
        def test_function():
            time.sleep(2)
        
        test_function()
        
        # Only new window should be closed
        initial_window.close.assert_not_called()
        new_window.close.assert_called_once()
    
    run_test()

def test_time_parsing():
    start_time = datetime.now()
    
    @lifetime("500ms")
    def quick_function():
        time.sleep(0.1)
    
    quick_function()
    duration = datetime.now() - start_time
    assert duration < timedelta(seconds=1) 