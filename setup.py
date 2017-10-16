from distutils.core import setup

setup(
    name='GAPAnalysis',
    version='0.3',
    packages=['gapanalysis'],
    author='Nathan M. Tarr',
    author_email='nmtarr@ncsu.edu',
    scripts=['bin/Update_Help_Files.py'],
    url='https://github.com/nmtarr/GAPAnalysis',
    license='LICENSE.txt',
    description='Functions for analyzing Gap Analysis Program habitat maps.',
    long_description=open('README.txt').read(),
    install_requires=[
            "pandas >= 0.20.1",
            "scipy >= 0.19.0",
    ],
)