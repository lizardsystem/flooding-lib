from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

urlpatterns = patterns(
    '',

    url(r'table/(?P<approvalobject_id>\d+)$',
        'lizard.flooding.tools.approvaltool.views.approvaltable_page',
        name='flooding_tools_approval_table'
        ),

    
)
