import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'pyramid_chameleon',
    'zope.interface',
    'waitress',
    'requests'
    ]

try:
    README = open(os.path.join(here, 'readme.rst')).read()
except:
    README = ''

setup(name='outpost',
      version='0.3.5',
      description='Application level proxy server',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Testing",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: BSD License"
        ],
      author='Arndt Droullier, Nive GmbH',
      author_email='info@nive.co',
      url='https://niveapps.com',
      keywords='server proxy development cors web pyramid',
      packages=find_packages(),
      include_package_data=True,
      license='BSD 3',
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="outpost",
      entry_points = """\
        [pyramid.scaffold]
        outpost=outpost.scaffolds:DefaultTemplate
      """
)

