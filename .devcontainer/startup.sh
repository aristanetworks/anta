#!/bin/sh

# echo "Configure direnv"
# echo "eval \"$(direnv hook bash)\"" >> ~/.bashrc

echo "Installing ANTA package from git"
pip install -e .

echo "Installing development tools"
pip install -e ".[dev]"
