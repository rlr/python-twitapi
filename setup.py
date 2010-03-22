#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup, find_packages
 
setup(name="twitapi",
      version="0.1",
      description="Python client library for the Twitter API.",
      author="Ricky Rosario",
      author_email="rickyrosario@gmail.com",
      url="http://github.com/rlr/python-twitapi",
      packages = find_packages(),
      install_requires = ['httplib2', 'oauth2'],
      license = "MIT License",
      keywords="twitter, oauth",
      zip_safe = True,
      tests_require=[])
