from setuptools import setup, find_packages
from pathlib import Path

package_name = 'sqrbotjr'
description = 'Second generation SQuaRE Slack bot designed around Kafka.'
author = 'Association of Universities for Research in Astronomy'
author_email = 'sqre-admin@lists.lsst.org'
license = 'MIT'
url = 'https://github.com/lsst-sqre/sqrbot-jr'
pypi_classifiers = [
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.7'
]
keywords = ['lsst', 'slack']
readme = Path(__file__).parent / 'README.rst'

# Core dependencies
install_requires = [
    'aiodns==1.1.1',
    'aiohttp==3.5.0',
    'cchardet==2.1.4',
    'structlog==18.2.0',
    'colorama==0.4.1',  # used by structlog
    'click>=6.7,<7.0',
    'fastavro==0.21.16',
    'kafkit==0.1.0',
    'aiokafka==0.5.0',
    'confluent-kafka==0.11.6',
]

# Test dependencies
tests_require = [
    'pytest==4.2.0',
    'pytest-flake8==1.0.4',
    'aiohttp-devtools==0.11',
]
tests_require += install_requires

# Sphinx documentation dependencies
docs_require = [
    'documenteer[pipelines]>=0.4.0,<0.5.0',
]

# Optional dependencies (like for dev)
extras_require = {
    # For development environments
    'dev': tests_require + docs_require
}

# Setup-time dependencies
setup_requires = [
    'pytest-runner>=4.2.0,<5.0.0',
    'setuptools_scm',
]

setup(
    name=package_name,
    description=description,
    long_description=readme.read_text(),
    author=author,
    author_email=author_email,
    url=url,
    license=license,
    classifiers=pypi_classifiers,
    keywords=keywords,
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'sqrbot = sqrbot.cli:main'
        ]
    },
    use_scm_version=True,
    include_package_data=True
)
