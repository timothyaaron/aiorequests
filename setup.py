from setuptools import find_packages, setup
import os.path

with open(os.path.join(
        os.path.dirname(__file__),
        "aiorequests", "_version")) as ver:
    __version__ = ver.readline().strip()

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: Implementation :: CPython",
]

with open('README.rst') as f:
    readme = f.read()


setup(
    name="aiorequests",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "aiohttp", "requests",
    ],
    package_data={"treq": ["_version"]},
    author="Jonathan Sandoval",
    author_email="jsandoval@utp.edu.co",
    classifiers=classifiers,
    description="A requests-like API built on top of aiohttp client",
    license="MIT/X",
    url="http://github.com/jsandovalc/aiorequests",
    long_description=readme
)
