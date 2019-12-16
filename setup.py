from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='sophos_central_api_connector',
      version='0.1.0',
      description='Sophos Central API Connector',
      author='Mark Lanczak-Faulds',
      author_email='mark.lanczak-faulds@sophos.com',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/sophos-cybersecurity/sophos-central-api-connector",
      include_package_data=True,
      setup_requires=["setuptools_scm"],
      packages=find_packages(),
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
       ],
      python_requires='>=3.6',
      install_requires=['boto3==1.10.36',
                        'botocore==1.13.36',
                        'certifi==2019.11.28',
                        'chardet==3.0.4',
                        'docutils==0.15.2',
                        'idna==2.8',
                        'jmespath==0.9.4',
                        'python-dateutil==2.8.1',
                        'requests==2.22.0',
                        's3transfer==0.2.1',
                        'six==1.13.0',
                        'urllib3==1.25.7'],
      )