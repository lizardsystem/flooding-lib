#!c:/python25/python.exe
# -*- coding: utf-8 -*-
#***********************************************************************
#*   
#***********************************************************************
#
# This file is part of Lizard Flooding 2.0.
#
# Lizard Flooding 2.0 is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Lizard Flooding 2.0 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lizard Flooding 2.0.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Copyright 2008, 2009 Mario Frasca
#
#***********************************************************************
# this module defines the properties of the database connection.
#
# $Id$
#
# initial programmer :  Mario Frasca
# initial date       :  20080808
#***********************************************************************

__revision_local__ = "$Rev$"[6:-2]

DATABASE_NAME = 'lizardweb'
DATABASE_USER = 'lizard'
DATABASE_PASSWORD = 'lizard'
DATABASE_HOST = '127.0.0.1'
DATABASE_PORT = '5432'

if 0:
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        'django.contrib.markup',
        'django.contrib.gis.db',
        'django.contrib.gis',
        # 'nens.lizardweb.report',
        # 'nens.lizardweb.locationparameterhelper',
        'nens.lizardweb.flooding',
        # 'nens.lizardweb.registration',
        'nens.lizardweb.visualization',
        'nens.lizardweb.base',
        'nens.lizardweb.presentation',
        'django.contrib.databrowse',
    )

MEDIA_ROOT = '/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/LizardWeb/Trunk/System/resources/doc_root'
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/LizardWeb/Trunk/System/srcPython/lizard/templates',
    '/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/LizardWeb/Trunk/System/srcPython/lizard/report/templates',
    '/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/LizardWeb/Trunk/System/srcPython/lizard/locationparameterhelper/templates',
    '/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/LizardWeb/Trunk/System/srcPython/lizard/flooding/tools/templates'
)
STATIC_DOC_ROOT = '/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/LizardWeb/Trunk/System/resources/doc_root'
SYMBOLS_DIR = '/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/LizardWeb/Trunk/System/resources/symbols'
ATTACHMENTS_DIR = '/tmp/attachment'
