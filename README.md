# History
- 2016/Jul/25
  - start development
- 2017/May/13
  - Clean up for push to GitHub

# What is this?

## Intro

This python3 script operates git-log and write to XLSX file.
See "conf.example/arm64_watch.xlsx" for output example.

## Motivation

This python3 script is made to 2 purpose:
  1. A part of my work automation.
  2. A example of XLSXWRITER and git command usage.

So, sometimes engineers are requested to report some differences list with XLSX file.
(Especially, Japan managers ;p)

Copying GIT log information to XLSX by hand, is too hard and bore for me.
I want automate it, and create this.

# Getting started
See "conf.example/arm64_watch/arm64_watch.md".

# Script details
## Dependencies
- Host OS
  - Linux based OS
    - Tested : Ubuntu 14.04 x64
- Software
  - Python 3.x
    - Python library
      - XLSXWRITER (http://xlsxwriter.readthedocs.io/index.html)
        - $ sudo pip3 install XlsxWriter
  - git
  - expand (in coreutils)

## Script options
<<T.B.D.>>

## About configuration file
<<T.B.D.>>
