from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    '',

    url(r'^pyramid_parameters/$',
        'flooding_lib.tools.pyramids.views.pyramid_parameters',
        name='pyramids_parameters'),
    url(r'^animated_pyramid_parameters/$',
        'flooding_lib.tools.pyramids.views.animated_pyramid_parameters',
        name='animated_pyramids_parameters')
)
