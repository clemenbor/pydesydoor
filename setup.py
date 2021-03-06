from setuptools import setup, find_packages

setup(
    name='pydesydoor',
    version='1.0.0',
    description='A python API to DESY DOOR user portal',
    url='https://github.com/clemenbor/pydesydoor',
    author='Clemente Borges',
    author_email='clemente.borges@desy.de',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        # Licence is "Apache License, Version 2.0" but the PyPI classifers
        # do not give a way to distinguish versions of the Apache License
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=['requests', 'python-dotenv'],
    packages=find_packages(exclude=["examples"]),  # Don't include examples directory
)
