from django.urls import include, path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('join/', views.enter_code, name='enter_code'),
    path('new/', views.new_game, name='new_game'),
    re_path(r'^(?P<access_code>[a-zA-Z]{6})/', include([
        path('', views.join_game, name='join_game'),
        path('qr/', views.qr_code, name='qr_code'),
        path('results/', views.game_results, name='game_results'),
        path('observe/', include([
            path('', views.observe, name='observe'),
            path('status/', views.observe_status, name='observe_status'),
            path('start/', views.observe_start, name='observe_start'),
            path('cancel_game/', views.observe_cancel_game, name='observe_cancel_game'),
            path('next_game/', views.observe_next_game, name='observe_next_game'),
        ])),
        re_path(r'(?P<player_secret>[a-z]{8})/', include([
            path('', views.game, name='game'),
            path('status/', views.status, name='status'),
            path('start/', views.start, name='start'),
            path('leave/', views.leave, name='leave'),
            path('ready/', views.ready, name='ready'),
            path('next_game/', views.next_game, name='next_game'),
            path('cancel_game/', views.cancel_game, name='cancel_game'),
            re_path(r'^(?P<round_num>[1-5])/(?P<vote_num>[1-5])/', include([
                re_path(r'^vote/(?P<vote>(approve|reject|cancel))/$', views.vote, name='vote'),
                re_path(r'^choose/(?P<who>[0-9])/$', views.choose, name='choose'),
                re_path(r'^unchoose/(?P<who>[0-9])/$', views.unchoose, name='unchoose'),
                path('finalize_team/', views.finalize_team, name='finalize_team'),
                path('retract_team/', views.retract_team, name='retract_team'),
            ])),
            re_path(r'^mission/(?P<round_num>[1-5])/(?P<mission_action>(success|fail))/$', views.mission, name='mission'),
            re_path(r'^assassinate/(?P<target>[0-9])/$', views.assassinate, name='assassinate'),
        ])),
    ])),
]
