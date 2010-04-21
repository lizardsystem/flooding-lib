from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

urlpatterns = patterns(
    '',
    
    url(r'^$',
        'lizard.flooding.tools.views.index',
        name='flooding_tools'),    

    url(r'^export/', 
        include('lizard.flooding.tools.exporttool.urls')),
    
    url(r'^import/', 
        include('lizard.flooding.tools.importtool.urls')),
    
    url(r'^approval/', 
        include('lizard.flooding.tools.approvaltool.urls')),
    
)
