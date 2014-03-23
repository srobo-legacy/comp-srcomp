# SRComp

[![Build Status](https://travis-ci.org/PeterJCLaw/srcomp.png?branch=master)](https://travis-ci.org/PeterJCLaw/srcomp)

Yet Another attempt at some Competition Software for [Student Robotics](http://srobo.org).

## Requirements

* Python 2.7
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
