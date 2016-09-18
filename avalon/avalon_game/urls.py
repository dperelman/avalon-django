from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^join/$', views.enter_code, name='enter_code'),
    url(r'^new/$', views.new_game, name='new_game'),
    url(r'^(?P<access_code>[a-zA-Z]{6})/', include([
        url(r'^$', views.join_game, name='join_game'),
        url(r'^qr/$', views.qr_code, name='qr_code'),
        url(r'(?P<player_secret>[a-z]{8})/', include([
            url(r'^$', views.game, name='game'),
            url(r'^status/$', views.status, name='status'),
            url(r'^start/$', views.start, name='start'),
            url(r'^leave/$', views.leave, name='leave'),
            url(r'^ready/$', views.ready, name='ready'),
            url(r'^cancel_game/$', views.cancel_game, name='cancel_game'),
            url(r'^(?P<round_num>[1-5])/(?P<vote_num>[1-5])/', include([
                url(r'^vote/(?P<vote>(approve|reject|cancel))/$', views.vote, name='vote'),
                url(r'^choose/(?P<who>[0-9])/$', views.choose, name='choose'),
                url(r'^unchoose/(?P<who>[0-9])/$', views.unchoose, name='unchoose'),
                url(r'^finalize_team/$', views.finalize_team, name='finalize_team'),
                url(r'^retract_team/$', views.retract_team, name='retract_team'),
            ])),
            url(r'^mission/(?P<round_num>[1-5])/(?P<mission_action>(success|fail))/$', views.mission, name='mission'),
            url(r'^assassinate/(?P<target>[0-9])/$', views.assassinate, name='assassinate'),
        ])),
    ])),
]
