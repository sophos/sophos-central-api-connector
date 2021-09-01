import setuptools
from os import path

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(name='sophos_central_api_connector',
                 version='0.1.6',
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
                 install_requires=['boto3>=1.17.21',
                                   'botocore>=1.20.21',
                                   'certifi>=2020.12.5',
                                   'chardet>=4.0.0',
                                   'configparser>=5.0.2',
                                   'docutils>=0.16',
                                   'intelix>=0.1.2',
                                   'jmespath>=0.10.0',
                                   'python-dateutil>=2.8.1',
                                   'requests>=2.25.1',
                                   's3transfer>=0.3.4',
                                   'six>=1.15.0',
                                   'urllib3>=1.26.3'],
                 include_package_data=True)
