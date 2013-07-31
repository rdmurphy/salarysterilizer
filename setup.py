from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='salarysterilizer',
    version='0.0.1',
    description='Cleaning up salary data, one CSV at a time',
    long_description=readme,
    author='Ryan Murphy',
    author_email='rmurphy@texastribune.org',
    url='https://github.com/rdmurphy/salarysterilizer',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points = {
      'console_scripts': [
          'sterilize = salarysterilizer:main',
        ]
    },
    install_requires = [
        'csvkit>=0.5.0',
        'name-cleaver>=0.5.2'
    ],
)
