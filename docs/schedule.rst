Schedule
========

Match Slots
-----------

Each match is assigned a 'slot' during which it will occur. The times for
the slot are generally what is advertised as the match start time, even
though the game doesn't actually start until some way into the slot.

Match Periods
-------------

Matches are grouped into timing periods. Each period has a description,
planned start and end times, plus a time beyond which no further matches
may be scheduled.

Usually the latter time is after the scheduled end time so that it works
to allow for delays to introduce a small overrun if needed. If configured
thus, then a period which experiences no delays would end at the scheduled
end time.

**Note**: the end times represent the time that the last match in the period
can be scheduled to *start* rather then *finish*.


Delays
------

Arbitrary delays can be added to the system at any point. These work to
delay the matches that start (currently measured by their slot start)
by the given amount, and are cumulative over the course of a period.

Staging Deadline
----------------

The staging deadline can be set using the `staging_deadline` key of the
schedule file. This should contain the number of seconds before the start of a
match slot that the teams should be ready to enter the arena.
