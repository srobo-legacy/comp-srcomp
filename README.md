# SRComp

[![Build Status](https://travis-ci.org/PeterJCLaw/srcomp.png?branch=master)](https://travis-ci.org/PeterJCLaw/srcomp)

Yet Another attempt at some Competition Software for [Student Robotics](http://srobo.org).

This repository provides a python API to accessing information about the
state of the competition. That _compstate_ is stored as a collection of
YAML files in a git repository. This allows the state of the competition
to be managed in isolation from the software while still providing
consistent representations of that state.

## Usage

Python clients should submodule this repo and then import it.
Only the `SRComp` is class directly exposed, and it should be constructed
around the path to a local working copy of a _compstate repo_.

~~~
from srcomp import SRComp
comp = SRComp('/path/to/compstate')
~~~

Web clients should look at using the HTTP API provided by
[srcomp-http](https://www.studentrobotics.org/cgit/comp/srcomp-http.git)
rather than implementing their own intermediary.

See the [dummy-comp](https://www.studentrobotics.org/cgit/comp/dummy-comp.git)
for an example of the structure and values expected in a _compstate repo_.

## Requirements

* Python 2.7
* python-dateutil
* nose
* mock
* PyYAML

## Test with
`./run-tests`

## Scripts
* `./validate`: Validates that the directory given by the only argument
                is a valid competition state folder.
* `./convert-schedule`: Converts a schedule from being one match per line
                        with participants separated by pipes into a yaml
                        format similar to that used in schedule.yaml.
                        NB: it only outputs the 'matches' root key and
                        assumes two arenas 'A' and 'B' and for games with
                        four participants.
