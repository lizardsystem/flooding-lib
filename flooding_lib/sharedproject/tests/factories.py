# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

""" """

# Python 3 is coming
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import factory

from flooding_lib.sharedproject import models


class ProvinceFactory(factory.Factory):
    FACTORY_FOR = models.Province

    name = "Overijssel"
    statistics = None


class OwnerFactory(factory.Factory):
    FACTORY_FOR = models.Owner

    # Let's say that WGS is an owner, and its province is Overijssel
    name = "Waterschap Groot Salland"
    province = factory.SubFactory(ProvinceFactory)
