"""A clock to manage match periods."""

class OutOfTimeException(Exception):
    """
    An exception representing no more time available at the competition to run
    matches.
    """

    pass


class MatchPeriodClock(object):
    """
    A clock for use in scheduling matches within a ``MatchPeriod``.

    It is generally expected that the time information here will be in the form
    of ``datetime`` and ``timedelta`` instances, though any data which can be
    compared and added appropriately should work.

    Delay rules:

    - Only delays which are scheduled after the start of the given period will
      be considered.
    - Delays are cumilative.
    - Delays take effect as soon as their ``time`` is reached.
    """

    def __init__(self, period, delays):
        """Create a new clock for the given period and collection of delays."""
        self._period = period

        # Only consider delays which are at the start of the period or later
        self._delays = [d for d in delays if d.time >= period.start_time]
        # Sort by when the delays occur
        self._delays.sort(key = lambda d: d.time)

        # The current time, including any delays
        self._current_time = period.start_time

        # The total applied delay
        self._total_delay = None

        # Apply any delays which occur at the start
        self._apply_delays()

    @property
    def current_time(self):
        """
        Get the apparent current time. This is a combination of the time which
        has passed (through calls to ``advance_time``) and the delays which
        have occurred.

        Will raise an ``OutOfTimeException`` if either:

        - the end of the period has been reached (i.e: the sum of durations
          passed to ``advance_time`` has exceeded the planned duration of the
          period), or
        - the maximum end of the period has been reached (i.e: the current time
          would be after the period's ``max_end_time``).
        """

        ct = self._current_time

        # Ensure we haven't exceeded the maximum time limit
        # (if we have then matches will get pushed into the next period)
        if ct > self._period.max_end_time:
            # we've filled this up to the maximum end time
            raise OutOfTimeException()

        # Ensure we haven't attempted to pack in more time than will
        # fit in this period
        if self._time_without_delays() > self._period.end_time:
            # we've filled up this period
            raise OutOfTimeException()

        return ct

    def advance_time(self, duration):
        """
        Make a given amount of time pass. This is expected to be called after
        scheduling some matches in order to move to the next timeslot.

        .. note::
           It is assumed that the duration value will always be 'positive',
           i.e. that time will not go backwards. The results of the duration
           valuebeing 'negative' are undefined.
        """

        self._current_time += duration
        self._apply_delays()

    def _apply_delays(self):
        delays = self._delays
        while len(delays) and delays[0].time <= self._current_time:
            self._apply_delay(delays.pop(0).delay)

    def _apply_delay(self, delay):
        self._current_time += delay

        if self._total_delay is None:
            self._total_delay = delay
        else:
            self._total_delay += delay

    def _time_without_delays(self):
        if self._total_delay is None:
            return self._current_time
        else:
            return self._current_time - self._total_delay

    def iterslots(self, slot_duration):
        """
        Iterate through all the available timeslots of the given size within
        the ``MatchPeriod``, taking into account delays.

        This is equivalent to checking the current_time and repeatedly calling
        ``advance_time`` with the given duration. As a result, it is safe to
        call ``advance_time`` between iterations if additional gaps between
        slots are needed.
        """

        try:
            while True:
                yield self.current_time
                self.advance_time(slot_duration)
        except OutOfTimeException:
            # Reached the end of the period
            pass
