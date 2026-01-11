from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from germanium.tools import (  # pylint: disable=E0401
    assert_equal,
    assert_is_none,
    assert_raises,
)
from test_chamber.models import BackendUser, FrontendUser  # pylint: disable=E0401

from chamber.multidomains.auth.backends import GetUserMixin
from chamber.multidomains.domain import (
    Domain,
    get_current_domain,
    get_domain,
    get_domain_choices,
    get_user_class,
)
from chamber.multidomains.urlresolvers import reverse


class MultidomainsTestCase(TestCase):
    def test_get_domain_choices(self):
        choices = get_domain_choices()
        assert_equal(len(choices), 2)
        assert_equal(choices[0][1], "backend")
        assert_equal(choices[1][1], "frontend")
        assert_equal(choices[0][0], 1)
        assert_equal(choices[1][0], 2)

    def test_get_current_user_class(self):
        assert_equal(get_user_class(), BackendUser)

    def test_get_user_class(self):
        assert_equal(get_domain(settings.BACKEND_SITE_ID).user_class, BackendUser)
        assert_equal(get_domain(settings.FRONTEND_SITE_ID).user_class, FrontendUser)

    def test_get_current_domain(self):
        assert_equal(get_current_domain().name, "backend")

    def test_get_domain(self):
        assert_equal(get_domain(settings.BACKEND_SITE_ID).name, "backend")
        assert_equal(get_domain(settings.FRONTEND_SITE_ID).name, "frontend")
        assert_raises(ImproperlyConfigured, get_domain, 3)

    def test_get_domain_url(self):
        assert_equal(get_domain(settings.BACKEND_SITE_ID).url, "http://localhost:8000")
        assert_equal(get_domain(settings.FRONTEND_SITE_ID).url, "https://localhost")

    def test_new_domain_port(self):
        assert_equal(
            Domain(
                "testA",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="http",
                hostname="localhost",
            ).port,
            80,
        )
        assert_equal(
            Domain(
                "testB",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="https",
                hostname="localhost",
            ).port,
            443,
        )
        assert_equal(
            Domain(
                "testC",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="http",
                hostname="localhost",
                port=443,
            ).port,
            443,
        )
        assert_equal(
            Domain(
                "testD",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="https",
                hostname="localhost",
                port=80,
            ).port,
            80,
        )
        assert_raises(
            ImproperlyConfigured,
            Domain,
            "testF",
            "dj.backend_urls",
            "test_chamber.BackendUser",
            protocol="hbbs",
            hostname="localhost",
        )
        assert_equal(
            Domain(
                "testD",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                url="https://localhost:80",
            ).port,
            80,
        )
        assert_equal(
            Domain(
                "testD",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                url="https://localhost",
            ).port,
            443,
        )

        assert_equal(
            Domain(
                "testA",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="http",
                hostname="localhost",
            ).url,
            "http://localhost",
        )
        assert_equal(
            Domain(
                "testB",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="https",
                hostname="localhost",
            ).url,
            "https://localhost",
        )
        assert_equal(
            Domain(
                "testC",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="http",
                hostname="localhost",
                port=443,
            ).url,
            "http://localhost:443",
        )
        assert_equal(
            Domain(
                "testD",
                "dj.backend_urls",
                "test_chamber.BackendUser",
                protocol="https",
                hostname="localhost",
                port=80,
            ).url,
            "https://localhost:80",
        )

    def test_reverse(self):
        assert_equal(reverse("current-datetime"), "/current_time_backend/")
        assert_equal(
            reverse("current-datetime", site_id=settings.BACKEND_SITE_ID),
            "/current_time_backend/",
        )
        assert_equal(
            reverse("current-datetime", site_id=settings.FRONTEND_SITE_ID),
            "/current_time_frontend/",
        )

        assert_equal(
            reverse(
                "current-datetime", site_id=settings.BACKEND_SITE_ID, add_domain=True
            ),
            "http://localhost:8000/current_time_backend/",
        )
        assert_equal(
            reverse(
                "current-datetime", site_id=settings.FRONTEND_SITE_ID, add_domain=True
            ),
            "https://localhost/current_time_frontend/",
        )

        assert_equal(
            reverse(
                "current-datetime",
                site_id=settings.BACKEND_SITE_ID,
                add_domain=True,
                urlconf="dj.frontend_urls",
            ),
            "http://localhost:8000/current_time_frontend/",
        )
        assert_equal(
            reverse(
                "current-datetime",
                site_id=settings.FRONTEND_SITE_ID,
                add_domain=True,
                urlconf="dj.backend_urls",
            ),
            "https://localhost/current_time_backend/",
        )

        assert_equal(
            reverse("current-datetime", qs_kwargs={"a": 1}),
            "/current_time_backend/?a=1",
        )

        assert_raises(ImproperlyConfigured, reverse, "current-datetime", site_id=3)

    def test_domain_user_model_columns_defaults_to_empty_list(self):
        domain = Domain(
            "test",
            "dj.backend_urls",
            "test_chamber.BackendUser",
            protocol="http",
            hostname="localhost",
        )
        assert_equal(domain.user_model_columns, [])

    def test_domain_user_model_columns_is_set_when_provided(self):
        columns = ["id", "username", "email"]
        domain = Domain(
            "test",
            "dj.backend_urls",
            "test_chamber.BackendUser",
            protocol="http",
            hostname="localhost",
            user_model_columns=columns,
        )
        assert_equal(domain.user_model_columns, columns)

    def test_domain_user_model_columns_none_becomes_empty_list(self):
        domain = Domain(
            "test",
            "dj.backend_urls",
            "test_chamber.BackendUser",
            protocol="http",
            hostname="localhost",
            user_model_columns=None,
        )
        assert_equal(domain.user_model_columns, [])


class GetUserMixinTestCase(TestCase):
    def test_get_user_returns_user_when_exists(self):
        user = BackendUser.objects.create()
        mixin = GetUserMixin()
        result = mixin.get_user(user.pk)
        assert_equal(result.pk, user.pk)

    def test_get_user_returns_none_when_user_does_not_exist(self):
        mixin = GetUserMixin()
        result = mixin.get_user(99999)
        assert_is_none(result)

    def test_get_user_uses_only_method_when_columns_specified(self):
        user = BackendUser.objects.create()
        columns = ["id", "password"]
        domain = Domain(
            "test",
            "dj.backend_urls",
            "test_chamber.BackendUser",
            protocol="http",
            hostname="localhost",
            user_model_columns=columns,
        )

        with patch(
            "chamber.multidomains.auth.backends.get_current_domain", return_value=domain
        ):
            mixin = GetUserMixin()
            result = mixin.get_user(user.pk)
            assert_equal(result.pk, user.pk)
            deferred_fields = result.get_deferred_fields()
            assert "id" not in deferred_fields
            assert "password" not in deferred_fields
            assert len(deferred_fields) > 0

    def test_get_user_does_not_use_only_method_when_columns_empty(self):
        user = BackendUser.objects.create()
        domain = Domain(
            "test",
            "dj.backend_urls",
            "test_chamber.BackendUser",
            protocol="http",
            hostname="localhost",
            user_model_columns=[],
        )

        with patch(
            "chamber.multidomains.auth.backends.get_current_domain", return_value=domain
        ):
            mixin = GetUserMixin()
            result = mixin.get_user(user.pk)
            assert_equal(result.pk, user.pk)
            deferred_fields = result.get_deferred_fields()
            assert len(deferred_fields) == 0
