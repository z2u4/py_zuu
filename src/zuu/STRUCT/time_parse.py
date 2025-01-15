from datetime import datetime
import time


def time_parse(time_str: str | float | int):
    """
    Parse a time string or timestamp into a datetime object.

    Args:
        time_str: Input time as either:
            - A string with time units (e.g., "500ms", "1h", "30min")
            - A string parseable by dateparser
            - A cron expression string
            - A float timestamp

    Supported time units:
        - ms, milliseconds
        - s, sec, seconds
        - m, min, minutes
        - h, hr, hrs, hours
        - d, days
        - w, weeks

    Returns:
        datetime: The parsed datetime object
        
    Raises:
        ImportError: If required modules dateparser or croniter are not installed
        ValueError: If the time string cannot be parsed
    """
    from datetime import datetime, timedelta
    import re

    # Handle numeric timestamps
    if isinstance(time_str, (int, float)) or (
        isinstance(time_str, str)
        and time_str.count(".") <= 1
        and time_str.replace(".", "").isdigit()
    ):
        return datetime.fromtimestamp(float(time_str))

    # Handle string inputs
    if isinstance(time_str, str):
        # Try parsing as time units
        time_units = {
            'ms': ('milliseconds', ['ms', 'millisecond', 'milliseconds']),
            's': ('seconds', ['s', 'sec', 'secs', 'second', 'seconds']),
            'm': ('minutes', ['m', 'min', 'mins', 'minute', 'minutes']),
            'h': ('hours', ['h', 'hr', 'hrs', 'hour', 'hours']),
            'd': ('days', ['d', 'day', 'days']),
            'w': ('weeks', ['w', 'week', 'weeks'])
        }

        # Clean up input string
        time_str = time_str.lower().strip()
        
        # Match number and unit (e.g., "500ms", "1.5h", "2 hours")
        match = re.match(r'^([\d.]+)\s*([a-z]+)$', time_str)
        if match:
            value, unit = match.groups()
            try:
                value = float(value)
                
                # Find matching unit
                for base_unit, (delta_attr, variants) in time_units.items():
                    if unit in variants:
                        kwargs = {delta_attr: value}
                        return datetime.now() + timedelta(**kwargs)
            except ValueError:
                pass

        # Try parsing as cron expression
        if any(c in time_str for c in "*/,"):
            try:
                from croniter import croniter
            except ImportError:
                raise ImportError("croniter module is required for cron expression parsing")
                
            try:
                base = datetime.now()
                cron = croniter(time_str, base)
                return cron.get_next(datetime)
            except ValueError:
                pass

        # Try parsing with dateparser
        try:
            import dateparser
        except ImportError:
            raise ImportError("dateparser module is required for natural language date parsing")
            
        parsed = dateparser.parse(time_str)
        if parsed:
            return parsed

    raise ValueError(f"Could not parse time string: {time_str}")

def time_sleep(time_str: str | float | int):
    target_time = time_parse(time_str)
    sleep_duration = (target_time - datetime.now()).total_seconds()
    if sleep_duration > 0:
        time.sleep(sleep_duration)
