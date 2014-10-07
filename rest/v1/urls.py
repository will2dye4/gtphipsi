from django.conf.urls.defaults import patterns, url, include

from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = patterns('gtphipsi.rest.v1.views',
    url(r'^auth/', obtain_auth_token, name='api_auth')
)

urlpatterns += patterns('',
     url(r'^brothers/', include('gtphipsi.rest.v1.brothers.urls')),
     url(r'^chapter/', include('gtphipsi.rest.v1.chapter.urls')),
     url(r'^forums/', include('gtphipsi.rest.v1.forums.urls')),
     url(r'^officers/', include('gtphipsi.rest.v1.officers.urls')),
     url(r'^rush/', include('gtphipsi.rest.v1.rush.urls'))
)