---
name: Bug report
about: Report something broken in FlowIndex
title: "[bug] "
labels: bug
body:
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
    validations:
      required: true
  - type: textarea
    id: reproduce
    attributes:
      label: Steps to reproduce
      placeholder: |
        flowindex init
        flowindex scan
        ...
    validations:
      required: true
  - type: input
    id: version
    attributes:
      label: FlowIndex version
      placeholder: pip show flowindex
  - type: input
    id: python
    attributes:
      label: Python version
      placeholder: python --version
