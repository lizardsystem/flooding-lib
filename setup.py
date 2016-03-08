from setuptools import setup
import os.path

version = '3.32'

long_description = '\n\n'.join([
    open('README.txt').read(),
    open(os.path.join('flooding_lib', 'USAGE.txt')).read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'Django >= 1.4, < 1.7',
    'iso8601',
    'django-nose',
    'django-markdown-deux',
    'lizard-worker >= 0.11',
    'django-treebeard',
    'django-extensions',
    'django-appconf',
    'south',
    'matplotlib',
    'nens',
    'GDAL',
    'django-debug-toolbar',
    'factory-boy',
    'mock',
    'xlrd',
    'xlwt',
    'lizard_ui',
    'django-excel-response',
    'gislib',
    'pyproj',
    'Flask',
    ],

tests_require = [
    ]

setup(name='flooding-lib',
      version=version,
      description="All apps needed for the Flooding website",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='Bastiaan Roos',
      author_email='bastiaan.roos@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['flooding_lib',
                'flooding_presentation',
                'flooding_visualization',
                'flooding_base',
                'raster_server'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
              'flask=raster_server.server:run',
          ]},
      )
