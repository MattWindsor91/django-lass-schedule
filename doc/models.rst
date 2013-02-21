======
Models
======

*schedule* provides multiple data models for defining schedules.  The models
constitute the lowest level of the schedule system; every other part of the
schedule is based on the data models.

It follows a hierarchical model in which shows are comprised of zero or more
*seasons*, which in turn are programmed into zero or more *timeslots*.  It
also supports the concept of *filler shows*, which are explained later,
implemented as a special case of ordinary show.

Each season has an assigned *term*, which is a holdover from the URY
scheduling system.

Shows are assigned specific *types*, which define whether they appear on the
schedule and show lists, as well as other parameters.

F

.. toctree::
    :maxdepth: 2

    terms
    shows
    types
    blocks
