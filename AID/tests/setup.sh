#!/bin/bash
REPORT_HTML="/home/wangbo/AID/report/report.html"
pytest -s -v --html="$REPORT_HTML" --self-contained-html