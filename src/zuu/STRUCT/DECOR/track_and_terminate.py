import threading
import re
from functools import wraps
from datetime import datetime
from ..time_parse import time_parse

def lifetime(
    timestr: str,
    diffInit: bool = True,
    globs: list[str] = [],
    usePsutil: bool = True,
    usePygetwindow: bool = True,
):
    def decorator(func):
        # Store initial state if diffInit is True
        initial_windows = set()
        initial_procs = set()
        if diffInit:
            if usePygetwindow:
                import pygetwindow as gw
                initial_windows = {win._hWnd for win in gw.getAllWindows()}
            if usePsutil:
                import psutil
                initial_procs = {proc.pid for proc in psutil.Process().children(recursive=True)}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get target termination time
            target_time = time_parse(timestr)

            # Start the function in a separate thread
            result = [None]
            exception = [None]
            
            def run_func():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=run_func)
            thread.daemon = True
            thread.start()

            # Wait until target time
            while datetime.now() < target_time and thread.is_alive():
                thread.join(timeout=0.1)

            # If thread is still running at target time, terminate
            if thread.is_alive():
                # Track which globs were matched by pygetwindow
                matched_globs = set()

                if usePygetwindow:
                    import pygetwindow as gw
                    current_windows = gw.getAllWindows()
                    for window in current_windows:
                        # Skip if using diffInit and window existed before
                        if diffInit and window._hWnd in initial_windows:
                            continue
                            
                        window_title = window.title.lower()
                        for glob_pattern in globs:
                            regex_pattern = glob_pattern.replace('*', '.*').replace('?', '.').lower()
                            if re.search(regex_pattern, window_title):
                                matched_globs.add(glob_pattern)
                                try:
                                    window.close()
                                except: #noqa
                                    pass

                if usePsutil:
                    import psutil
                    current_process = psutil.Process()
                    for proc in current_process.children(recursive=True):
                        # Skip if using diffInit and process existed before
                        if diffInit and proc.pid in initial_procs:
                            continue
                            
                        try:
                            # Only check globs that weren't matched by pygetwindow
                            proc_name = proc.name().lower()
                            proc_cmdline = ' '.join(proc.cmdline()).lower()
                            
                            for glob_pattern in globs:
                                if glob_pattern in matched_globs:
                                    continue
                                    
                                regex_pattern = glob_pattern.replace('*', '.*').replace('?', '.').lower()
                                if (re.search(regex_pattern, proc_name) or 
                                    re.search(regex_pattern, proc_cmdline)):
                                    proc.terminate()
                                    try:
                                        proc.wait(timeout=3)
                                    except psutil.TimeoutExpired:
                                        proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                # Re-raise any exception that occurred
                if exception[0]:
                    raise exception[0]
                
                return result[0]

            # Return the result if completed in time
            if exception[0]:
                raise exception[0]
            return result[0]

        return wrapper
    
    return decorator