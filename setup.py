from setuptools import setup
import os.path

version = '5.0.7'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open(os.path.join('flooding_lib', 'USAGE.txt')).read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'Django == 1.6.6',
    'Flask',
    'django-celery',
    'django-appconf',
    'django-debug-toolbar',
    'django-excel-response',
    'django-extensions',
    'django-markdown-deux',
    'django-nose',
    'django-treebeard',
    'factory-boy',
    'flask',
    'gdal',
    'gislib',
    'gunicorn',
    'iso8601',
    'lizard-raster',
    'lizard-worker',
    # mapnik deliberately not here, buildout / syseggrecipe don't work
    'matplotlib',
    'mock',
    'nens',
    'netCDF4',
    'numpy',
    'psycopg2',
    'pyproj',
    'raven',
    'scipy',
    'south',
    'supervisor',
    'xlrd',
    'xlwt',
    ],

tests_require = [
    'ipython',
    'ipdb',
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
              'runflask=raster_server.server:run',
          ]},
      )
