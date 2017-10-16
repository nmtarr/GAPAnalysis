from setuptools import setup, find_packages

setup(
    name='GAPAnalysis',
    version='0.3',
    packages=find_packages(exclude=[docs, tests],
    author='Nathan M. Tarr',
    author_email='nmtarr@ncsu.edu',
    scripts=['bin/Update_Help_Files.py'],
    url='https://github.com/nmtarr/GAPAnalysis',
    license='LICENSE.txt',
    description='Functions for analyzing Gap Analysis Program habitat maps.',
    long_description=open('README.txt').read(),
    install_requires=["pandas >= 0.20.1","scipy >= 0.19.0"],
    classifiers=['Development Status :: 3 - Alpha',
    		'Programming Language :: Python :: 2.7'],
    keywords='USGS Gap Analysis Program',
    python_requires='==2.7',
    # Could the below be used to point to ScienceBase?
    #data_files=[('my_data', ['data/data_file'])],
)