#!/bin/bash
REPORT_HTML="/home/***/AID/report/report.html"
pytest -s -v --html="$REPORT_HTML" --self-contained-html