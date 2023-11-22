from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in condominium_ve/__init__.py
from condominium_ve import __version__ as version

setup(
	name="condominium_ve",
	version=version,
	description="Condominios para Venezuela",
	author="Datacomm, C.A.",
	author_email="oficinadatacomm@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
