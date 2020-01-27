#!/usr/bin/env python3
from setuptools import setup
from pathlib import Path
thisDir = Path(__file__).parent.absolute()

packageName = "wisent"

if __name__ == "__main__":
	setup(use_scm_version={
		"write_to": thisDir / packageName / "version.py",
		"write_to_template": 'PACKAGE="wisent"\nVERSION="{version}"\n',
	})
