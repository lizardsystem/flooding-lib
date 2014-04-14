from setuptools import setup
import os.path

version = '3.17.4dev'

long_description = '\n\n'.join([
    open('README.txt').read(),
    open(os.path.join('flooding_lib', 'USAGE.txt')).read(),
    open('TODO.txt').read(),
    open('CREDITS.txt').read(),
    open('CHANGES.txt').read(),
    ])

install_requires = [
    'Django',
    'django-staticfiles',
    'flooding-base >= 1.34',
    'lizard-worker >= 0.10',
    'django-treebeard',
    'django-extensions',
    'django-nose',
    'django-appconf',
    'nens',
    'GDAL',
    'django-debug-toolbar',
    'factory-boy',
    'mock',
    'xlrd',
    'xlwt',
    'lizard_ui',
    #'threedilib',
    'django-excel-response',
    'gislib',
#    'pyproj', # We do need it, but requiring it doesn't work well
    'Flask',
    ],

tests_require = [
    ]

setup(name='flooding-lib',
      version=version,
      description="TODO",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='TODO',
      author_email='TODO@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['flooding_lib',
                'flooding_presentation',
                'flooding_visualization',
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
