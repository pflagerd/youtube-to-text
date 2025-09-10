#!/bin/bash
""":"
which apt >/dev/null 2>&1 || (echo "This script only works on systems having the apt package manager" && exit 1)
if ! sudo apt list --installed 2>/dev/null | grep python3-pip >/dev/null 2>&1; then
  sudo apt install python3-pip -y >/dev/null 2>&1 || (echo "Something went wrong installing python3-pip" && exit 1)
fi
if ! sudo apt list --installed 2>/dev/null | grep python3-venv >/dev/null 2>&1; then
  sudo apt install python3-venv -y >/dev/null 2>&1 || (echo "Something went wrong installing python3-venv" && exit 1)
fi
pushd $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd) >/dev/null
if ! (which python3 >/dev/null && python3 --version | grep ' 3.' >/dev/null); then
  echo "You must have python 3 installed to run this."
  exit 1
fi
if ! [ -d .venv/ ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -r requirements.txt || (echo "Something went wrong pip installing requirements.txt" && exit 1)
popd >/dev/null
exec python3 "$0" "$@"
":"""

# Everything after this is ignored by bash,
# but Python sees it normally.
# -*- coding: utf-8 -*-
"""
Now we're inside Python
"""
print("Hello from test-auto-install.py!")
