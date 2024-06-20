import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='cba',
    version='1.3.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    license='ESA-PL Permissive – v2.4',
    description='CBA Benchmarking Testsuite.',
    long_description=README,
    author='EXPRIVIA SpA',
    author_email='cba-xpr at exprivia.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: ESA-PL Permissive – v2.4',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        'Topic :: System :: Benchmark',
    ],
    install_requires=[
        'PyYAML==5.4.1',
        'requests==2.27.1',
        'requests-oauthlib==1.3.1',
        'prefect==1.2.0',
        'typer==0.4.1',
        'Cerberus==1.3.4',
    ],
    tests_require=[
        'tox',
    ]
)
