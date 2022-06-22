import math
from apscheduler.triggers.interval import IntervalTrigger
import app.config as config


def modify_scheduler(time, job_name, time_type="seconds", margin=0):
    """Dynamically modifies the given job depending on how long the last
       job took to complete.

    Args:
        time (int, float): The amount of time elapsed from the start of the job
                    to the end of the job (in seconds)
        job_name (str): Then name of the APScheduler job to modify
        time_type (str): The unit of time that the scheduler uses for the job.
                    Valid inputs are 'seconds' or 'minutes'. Defaults to
                    'seconds'
        margin (int): A number of seconds or minutes, defined by time_type,
                    Used to calculate whether the time falls within an
                    acceptable range and determine if the interval needs to
                    change. Defaults to 0.

    Raises:
        TypeError: Time must be an int or float
        TypeError: Job Name must be a str
        TypeError: Time Type must be a str
        TypeError: Margin must be an int
        ValueError: Time must be a positive integer
        ValueError: Time Type must be 'seconds' or 'minutes'
        ValueError: Margin must be a positive integer or zero

    Returns:
        str: A message about whether the interval was modified or remains
             the same
    """
    if not isinstance(time, (int, float)):
        msg = str("Time must be an int or float, not {}").format(type(time))
        raise TypeError(msg)
    if not isinstance(job_name, str):
        msg = str("Job Name must be string, not {}").format(type(job_name))
        raise TypeError(msg)
    if not isinstance(time_type, str):
        msg = str("Time type must be string, not {}").format(type(time_type))
        raise TypeError(msg)
    if not isinstance(margin, int):
        msg = str("Time type must be string, not {}").format(type(margin))
        raise TypeError(msg)
    if time <= 0:
        msg = str("Time must be a positive int or float, not {}").format(time)
        raise ValueError(msg)
    if time_type not in ['seconds', 'minutes']:
        msg = str("Time type must be 'seconds' or 'minutes', not {}"
                  "").format(time_type)
        raise ValueError(msg)
    if margin < 0:
        msg = str("Margin must be a positive integer or zero, not {}"
                  "").format(margin)
        raise ValueError(msg)

    if time_type == "seconds":
        # If time_type is 'seconds' always round up to the nearest second
        time = math.ceil(time)
    elif time_type == "minutes":
        # If time_type is 'minutes', round to the nearest whole second
        time = round(time)

    # Get currently scheduled interval
    job = config.scheduler.get_job(job_name)
    if job:
        job_string = str(job.trigger).replace('[', '$').replace(']', '')
        job_details = job_string.split("$")
    else:
        msg = str("Job {} not found in the job store. No changes made."
                  "").format(job_name)
        return msg

    if "cron" in job_details:
        msg = str("{} job scheduled. Timing is {}. No changes will be made."
                  "").format(job_details[0], job_details[1])
        return msg
    elif "interval" in job_details:
        # job_type = job_details[0]
        interval_time = job_details[1].split(":")
        interval_hour = int(interval_time[0])
        interval_minute = int(interval_time[1])
        interval_second = int(interval_time[2])

    job_dict = {"job_id": job.id}

    # Convert everything to seconds so that we're dealing with a single type
    # of time increment.
    if interval_hour == 0 and interval_minute == 0:
        # Set interval to the seconds place
        interval = interval_second
    elif interval_hour == 0 and interval_second == 0:
        # Set interval to the minutes place. Multiply by 60 to get interval
        # in seconds. Multiply margin by 60 to get margin in seconds
        interval = interval_minute * 60
        margin = margin * 60

    if time >= interval - margin and time <= interval + margin:
        # Ex: Interval 15, margin 5, time 17
        # If 17 <= 20: True
        # If 17 >= 10: True
        # Time is within the margins and no changes need to be made.
        msg = str("Job interval and job runtime are within {} {} of "
                  "each other. No changes to interval."
                  "").format(margin, time_type)
        return msg

    new_interval = interval
    if interval + margin > time:
        # If the interval is greater than the time it took to run the process,
        # check to see how much more. Subtract the delta from the interval, but
        # then add in the margin.
        delta = interval - time
        if delta >= margin:
            new_interval = interval - delta + margin
        msg = str("Job {} interval is {} {} longer than the job "
                  "runtime. Reduced interval to {} {}."
                  "").format(job_name, int(delta), time_type,
                             new_interval, time_type)
    elif interval - margin < time:
        # If the interval is less than the time it took to run the process,
        # increase the interval. Add the delta from the interval, but
        # then subtract in the margin.
        delta = time - interval
        if delta <= margin:
            new_interval = interval + delta - margin
            # If the interval is less than 1 (minute or second), set the
            # interval to 1.
            if new_interval < 1:
                new_interval = 1
        msg = str("Job {} interval is {} {} shorter than the job "
                  "runtime. Increased interval to {} {}."
                  "").format(job_name, int(delta), time_type,
                             new_interval, time_type)
    else:
        msg = str("ERROR: Job interval {}, elapsed time {}"
                  "").format(interval, time)

    if time_type == 'minutes':
        new_interval = math.ceil(new_interval / 60)
    # job_dict[time_type] = new_interval
    trigger_dict = {time_type: new_interval}
    new_trigger = IntervalTrigger(**trigger_dict)
    job_dict['trigger'] = new_trigger
    config.scheduler.reschedule_job(**job_dict)
    return msg
