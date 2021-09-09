import setuptools

with open("README.md.md", "r", encoding="utf-8") as fh:
  long_description = fh.read()

setuptools.setup(
  name="streaminghub-pydfs",
  version="1.0.0",
  author="Yasith Jayawardana",
  author_email="yasith@cs.odu.edu",
  description="Python Library for using Dataset File System (DFS) in StreamingHub projects",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/nirdslab/streaminghub/tree/master/pydfs",
  project_urls={
    "Bug Tracker": "https://github.com/nirdslab/streaminghub/issues",
  },
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  package_dir={"": "src"},
  packages=setuptools.find_packages(where="src"),
  python_requires=">=3.6",
  install_requires=[
    'pylsl',
    'jsonschema',
  ],
)
