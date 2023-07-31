#!/bin/bash
export signed_cookie=thisisthesecretkey
cd "$(dirname "$0")"
python3 main.py
