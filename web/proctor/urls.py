from django.conf.urls import url
from . import views

app_name = 'proctor'
urlpatterns = [
    # Proctor API
    url(r'^check/(?P<pid>\w+)', views.CheckItem.as_view(), {'fix': False}),
    url(r'^fix/(?P<pid>\w+)', views.CheckItem.as_view(), {'fix': True}),
    url(r'^list', views.APIConditionList.as_view()),


    # Proctor web pages
    url(r'^(?P<model_name>\w+)$', views.ConditionList.as_view()),
    url(r'^(?P<model_name>\w+)/check_all$', views.CheckAll.as_view()),
    url(r'^(?P<model_name>\w+)/(?P<model_id>.+)$', views.ItemView.as_view()),
]