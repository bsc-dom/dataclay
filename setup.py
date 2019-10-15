from setuptools import setup, find_packages
import os 

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]
# parse_requirements
install_reqs = parse_requirements("./requirements.txt")

PYCLAY_VERSION = os.environ.get('PYCLAY_VERSION', 'trunk')
print("** USING PYCLAY VERSION = %s" % PYCLAY_VERSION)
setup(name='dataClay',
      version=PYCLAY_VERSION,
      install_requires=install_reqs,
      description='Python library for dataClay',
      packages=find_packages("src"),
      package_dir={'':'src'},
      package_data={
        # All .properties files are valuable "package data"
        '': ['*.properties'],
      },
      )

