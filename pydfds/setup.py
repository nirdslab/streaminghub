import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
  long_description = fh.read()

setuptools.setup(
  name="streaminghub-pydfds",
  version="1.0.0",
  author="Yasith Jayawardana",
  author_email="yasith@cs.odu.edu",
  description="Parser for Data Flow Description Schema (DFDS) metadata",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/nirdslab/streaminghub/tree/master/pydfds",
  project_urls={
    "Bug Tracker": "https://github.com/nirdslab/streaminghub/issues",
  },
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  package_dir={"pydfds": "./src"},
  packages=["pydfds"],
  python_requires=">=3.8",
  install_requires=[
    'pylsl',
    'jsonschema',
  ],
)
