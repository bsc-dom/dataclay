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

with open("VERSION.txt", "r") as version_file:
    version = version_file.read().strip()

setup(name='dataClay',
      version=version,
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

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate you support Python 3. These classifiers are *not*
          # checked by 'pip install'. See instead 'python_requires' below.
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3 :: Only',

      ],
      # Specify which Python versions you support. In contrast to the
      # 'Programming Language' classifiers above, 'pip install' will check this
      # and refuse to install the project if the version does not match. See
      # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
      python_requires='>=3.5, <4'
      )

