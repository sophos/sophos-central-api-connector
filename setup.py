import setuptools
from os import path

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(name='sophos_central_api_connector',
                 version='0.1.3',
                 description='Sophos Central API Connector',
                 author='Mark Lanczak-Faulds',
                 author_email='mark.lanczak-faulds@sophos.com',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                     "Operating System :: OS Independent",
                 ],
                 url="https://github.com/sophos-cybersecurity/sophos-central-api-connector",
                 setup_requires=["setuptools_scm"],
                 packages=['sophos_central_api_connector', 'sophos_central_api_connector.config'],
                 package_data={'sophos_central_api_connector': ['config/*']},
                 python_requires='>=3.6',
                 install_requires=['boto3>=1.16.2',
                                   'botocore>=1.19.2',
                                   'certifi>=2020.6.20',
                                   'chardet>=3.0.4',
                                   'configparser>=5.0.1',
                                   'docutils>=0.16',
                                   'idna>=2.10',
                                   'intelix>=0.1.2',
                                   'jmespath>=0.10.0',
                                   'python-dateutil>=2.8.1',
                                   'requests>=2.24.0',
                                   's3transfer>=0.3.3',
                                   'six>=1.15.0',
                                   'urllib3>=1.25.11'],
                 include_package_data=True)
