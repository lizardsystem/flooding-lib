from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(r'^pyramid_parameters/$',
        'flooding_lib.tools.pyramids.views.pyramid_parameters',
        name='pyramids_parameters'),
    url(r'^pyramid_value/$',
        'flooding_lib.tools.pyramids.views.pyramid_value',
        name='pyramid_value'),
    url(r'^animation_value/$',
        'flooding_lib.tools.pyramids.views.animation_value',
        name='animation_value')
)
