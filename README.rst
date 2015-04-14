SRComp
======

|Build Status| |Docs Status|

Yet Another attempt at some Competition Software for `Student
Robotics <http://srobo.org>`__.

This repository provides a python API to accessing information about the
state of the competition. That *compstate* is stored as a collection of
YAML files in a git repository. This allows the state of the competition
to be managed in isolation from the software while still providing
consistent representations of that state.

Usage
-----

Python clients should submodule this repo and then import it. Only the
``SRComp`` is class directly exposed, and it should be constructed
around the path to a local working copy of a *compstate repo*.

.. code:: python

    from srcomp import SRComp
    comp = SRComp('/path/to/compstate')

Web clients should look at using the HTTP API provided by
`srcomp-http <https://www.studentrobotics.org/cgit/comp/srcomp-http.git>`__
rather than implementing their own intermediary.

See the
`dummy-comp <https://www.studentrobotics.org/cgit/comp/dummy-comp.git>`__
for an example of the structure and values expected in a *compstate
repo*.

Requirements
------------

-  Python 2.7
-  python-dateutil
-  PyYAML
-  nose (for testing)
-  mock (for testing)

Test with
---------

``./run-tests``

Scripts
-------

-  ``./validate``: Validates that the directory given by the only
   argument is a valid competition state folder.
-  ``./convert-schedule``: Converts a schedule from being one match per
   line with participants separated by pipes into a yaml format similar
   to that used in schedule.yaml. NB: it only outputs the 'matches' root
   key and assumes two arenas 'A' and 'B' and for games with four
   participants.

.. |Build Status| image:: https://travis-ci.org/PeterJCLaw/srcomp.png?branch=master
   :target: https://travis-ci.org/PeterJCLaw/srcomp

.. |Docs Status| image:: https://readthedocs.org/projects/srcomp/badge/?version=latest
   :target: http://srcomp.readthedocs.org/
