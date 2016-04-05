#!/usr/bin/python3
"""Setup
"""
from setuptools import find_packages
from distutils.core import setup

version = "0.0.1"

with open('README.rst') as f:
    long_description = f.read()

setup(name='ofxstatement-polish',
      version=version,
      author="Jakub Janeczko",
      author_email="jjaneczk@gmail.com",
      url="https://github.com/jjajo/ofxstatement-polish",
      description=("Polish bank statement parsers"),
      long_description=long_description,
      license="GPLv3",
      keywords=["ofx", "banking", "statement"],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
          'Natural Language :: English',
          'Topic :: Office/Business :: Financial :: Accounting',
          'Topic :: Utilities',
          'Environment :: Console',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU Affero General Public License v3'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=["ofxstatement", "ofxstatement.plugins"],
      entry_points={
          'ofxstatement':
          ['banksmart = ofxstatement.plugins.banksmart:BankSMARTPlugin',
           'db.pl = ofxstatement.plugins.db_pl:DBPLPlugin',
           'mbank.pl = ofxstatement.plugins.mbank_pl:MBankPLPlugin',
           'millennium = ofxstatement.plugins.millennium:MillenniumPlugin',
           'paypal = ofxstatement.plugins.paypal:PaypalPlugin',
           'raiffeisen-polbank = ofxstatement.plugins.raiffeisen_polbank:RaiffeisenPolbankPlugin',
           'walutomat = ofxstatement.plugins.walutomat:WalutomatPlugin']
          },
      install_requires=['ofxstatement'],
      include_package_data=True,
      zip_safe=True
      )
