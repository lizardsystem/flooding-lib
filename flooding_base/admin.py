from django.contrib import admin

from flooding_base.models import Application
from flooding_base.models import Configuration
from flooding_base.models import DataSourceDummy
from flooding_base.models import DataSourceEI
from flooding_base.models import GroupConfigurationPermission
from flooding_base.models import Map
from flooding_base.models import Setting
from flooding_base.models import Site
from flooding_base.models import SubApplication
from flooding_base.models import Text


class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'datasourcetype', 'hasDataSource', )


class DataSourceEIAdmin(admin.ModelAdmin):
    list_display = ('configuration', 'id', 'connectorurl',
                    'databaseurl', 'databaseurltagname',
                    'usecustomfilterresponse')

admin.site.register(Application)
admin.site.register(Configuration, ConfigurationAdmin)
admin.site.register(DataSourceDummy)
admin.site.register(DataSourceEI, DataSourceEIAdmin)
admin.site.register(GroupConfigurationPermission)
admin.site.register(Map)
admin.site.register(Setting)
admin.site.register(Site)
admin.site.register(SubApplication)
admin.site.register(Text)
