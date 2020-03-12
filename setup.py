from setuptools import setup, find_packages
import os 

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]
# parse_requirements
install_reqs = parse_requirements("./requirements.txt")

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='dataClay',
      version="2.4.dev",
      install_requires=install_reqs,
      description='Python library for dataClay',
      packages=find_packages("src"),
      package_dir={'':'src'},
      package_data={
        # All .properties files are valuable "package data"
        '': ['*.properties'],
      },
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://www.bsc.es/dataclay",
      project_urls={
          'Documentation': 'https://pyclay.readthedocs.io/en/latest/',
          'Source': 'https://github.com/bsc-dom/pyclay',
      },
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Science/Research",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: BSD License",
          "Programming Language :: Python",
          "Topic :: Database :: Database Engines/Servers",
          "Topic :: System :: Distributed Computing",
          "Topic :: Software Development :: Libraries :: Application Frameworks",
      ],
      )

