import django
import factory
import unittest
import warnings

from contextlib import contextmanager
from distutils.version import LooseVersion

import sys

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from test_plus.test import (
    CBVTestCase,
    NoPreviousResponse,
    TestCase,
    APITestCase,
)
from test_plus.compat import DRF

from .forms import TestNameForm
from .models import Data
from .views import (
    CBDataView,
    CBTemplateView,
    CBView,
)

DJANGO_16 = LooseVersion(django.get_version()) >= LooseVersion('1.6')
DJANGO_18 = LooseVersion(django.get_version()) >= LooseVersion('1.8')

if DJANGO_16:
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    from django.contrib.auth.models import User


@contextmanager
def redirect_stdout(new_target):
    old_target, sys.stdout = sys.stdout, new_target
    try:
        yield new_target
    finally:
        sys.stdout = old_target


class UserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user{}'.format(n))
    email = factory.Sequence(lambda n: 'user{}@example.com'.format(n))

    class Meta:
        model = User


class TestPlusUserFactoryOption(TestCase):
    user_factory = UserFactory

    def test_make_user_factory(self):
        u1 = self.make_user('factory')
        self.assertEqual(u1.username, 'factory')


class TestPlusViewTests(TestCase):

    def test_get(self):
        res = self.get('view-200')
        self.assertEqual(res.status_code, 200)

        url = self.reverse('view-200')
        res = self.get(url)
        self.assertEqual(res.status_code, 200)

    def test_print_form_errors(self):

        with self.assertRaisesMessage(Exception, 'print_form_errors requires the response_or_form argument to either be a Django http response or a form instance.'):
            self.print_form_errors('my-bad-argument')

        form = TestNameForm(data={})
        self.assertFalse(form.is_valid())

        output = StringIO()
        with redirect_stdout(output):
            self.print_form_errors(form)
        output = output.getvalue().strip()
        self.assertTrue('This field is required.' in output)

        self.post('form-errors')
        self.response_200()
        output = StringIO()
        with redirect_stdout(output):
            self.print_form_errors()
        output = output.getvalue().strip()
        self.assertTrue('This field is required.' in output)

    def test_get_follow(self):
        # Expect 302 status code
        res = self.get('view-redirect')
        self.assertEqual(res.status_code, 302)
        # Expect 200 status code
        url = self.reverse('view-redirect')
        res = self.get(url, follow=True)
        self.assertEqual(res.status_code, 200)

    def test_get_query(self):
        res = self.get('view-200', data={'query': 'foo'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.request['QUERY_STRING'], 'query=foo')

    def test_post(self):
        url = self.reverse('view-200')
        data = {'testing': True}
        res = self.post(url, data=data)
        self.assertTrue(res.status_code, 200)

    def test_post_follow(self):
        url = self.reverse('view-redirect')
        data = {'testing': True}
        # Expect 302 status code
        res = self.post(url, data=data)
        self.assertTrue(res.status_code, 302)
        # Expect 200 status code
        res = self.post(url, data=data, follow=True)
        self.assertTrue(res.status_code, 200)

    def test_put(self):
        url = self.reverse('view-200')
        res = self.put(url)
        self.assertTrue(res.status_code, 200)

    def test_put_follow(self):
        url = self.reverse('view-redirect')
        # Expect 302 status code
        res = self.put(url)
        self.assertTrue(res.status_code, 302)
        # Expect 200 status code
        res = self.put(url, follow=True)
        self.assertTrue(res.status_code, 200)

    def test_patch(self):
        url = self.reverse('view-200')
        res = self.patch(url)
        self.assertTrue(res.status_code, 200)

    def test_patch_follow(self):
        url = self.reverse('view-redirect')
        # Expect 302 status code
        res = self.patch(url)
        self.assertTrue(res.status_code, 302)
        # Expect 200 status code
        res = self.patch(url, follow=True)
        self.assertTrue(res.status_code, 200)

    def test_head(self):
        url = self.reverse('view-200')
        res = self.head(url)
        self.assertTrue(res.status_code, 200)

    def test_head_follow(self):
        url = self.reverse('view-redirect')
        # Expect 302 status code
        res = self.head(url)
        self.assertTrue(res.status_code, 302)
        # Expect 200 status code
        res = self.head(url, follow=True)
        self.assertTrue(res.status_code, 200)

    # def test_trace(self):
    #     url = self.reverse('view-200')
    #     res = self.trace(url)
    #     self.assertTrue(res.status_code, 200)
    #
    # def test_trace_follow(self):
    #     url = self.reverse('view-redirect')
    #     # Expect 302 status code
    #     res = self.trace(url)
    #     self.assertTrue(res.status_code, 302)
    #     # Expect 200 status code
    #     res = self.trace(url, follow=True)
    #     self.assertTrue(res.status_code, 200)

    def test_options(self):
        url = self.reverse('view-200')
        res = self.options(url)
        self.assertTrue(res.status_code, 200)

    def test_options_follow(self):
        url = self.reverse('view-redirect')
        # Expect 302 status code
        res = self.options(url)
        self.assertTrue(res.status_code, 302)
        # Expect 200 status code
        res = self.options(url, follow=True)
        self.assertTrue(res.status_code, 200)

    def test_delete(self):
        url = self.reverse('view-200')
        res = self.delete(url)
        self.assertTrue(res.status_code, 200)

    def test_delete_follow(self):
        url = self.reverse('view-redirect')
        # Expect 302 status code
        res = self.delete(url)
        self.assertTrue(res.status_code, 302)
        # Expect 200 status code
        res = self.delete(url, follow=True)
        self.assertTrue(res.status_code, 200)

    def test_get_check_200(self):
        res = self.get_check_200('view-200')
        self.assertTrue(res.status_code, 200)

    def test_response_200(self):
        res = self.get('view-200')
        self.response_200(res)

        # Test without response option
        self.response_200()

    def test_response_201(self):
        res = self.get('view-201')
        self.response_201(res)

        # Test without response option
        self.response_201()

    def test_response_301(self):
        res = self.get('view-301')
        self.response_301(res)

        # Test without response option
        self.response_301()

    def test_response_302(self):
        res = self.get('view-302')
        self.response_302(res)

        # Test without response option
        self.response_302()

    def test_response_400(self):
        res = self.get('view-400')
        self.response_400(res)

        # Test without response option
        self.response_400()

    def test_response_401(self):
        res = self.get('view-401')
        self.response_401(res)

        # Test without response option
        self.response_401()

    def test_response_403(self):
        res = self.get('view-403')
        self.response_403(res)

        # Test without response option
        self.response_403()

    def test_response_404(self):
        res = self.get('view-404')
        self.response_404(res)

        # Test without response option
        self.response_404()

    def test_response_405(self):
        res = self.get('view-405')
        self.response_405(res)

        # Test without response option
        self.response_405()

    def test_response_410(self):
        res = self.get('view-410')
        self.response_410(res)

        # Test without response option
        self.response_410()

    def test_make_user(self):
        """ Test make_user using django.contrib.auth defaults """
        u1 = self.make_user('u1')
        self.assertEqual(u1.username, 'u1')

    def test_make_user_with_perms(self):
        u1 = self.make_user('u1', perms=['auth.*'])
        expected_perms = [u'add_group', u'change_group', u'delete_group',
                          u'add_permission', u'change_permission', u'delete_permission',
                          u'add_user', u'change_user', u'delete_user']
        self.assertEqual(list(u1.user_permissions.values_list('codename', flat=True)), expected_perms)

        u2 = self.make_user('u2', perms=['auth.add_group'])
        self.assertEqual(list(u2.user_permissions.values_list('codename', flat=True)), [u'add_group'])

    def test_login_required(self):
        self.assertLoginRequired('view-needs-login')

        # Make a user and login with our login context
        self.make_user('test')
        with self.login(username='test', password='password'):
            self.get_check_200('view-needs-login')

    def test_login_other_password(self):
        # Make a user with a different password
        user = self.make_user('test', password='revsys')
        with self.login(user, password='revsys'):
            self.get_check_200('view-needs-login')

    def test_login_no_password(self):

        user = self.make_user('test')
        with self.login(username=user.username):
            self.get_check_200('view-needs-login')

    def test_login_user_object(self):

        user = self.make_user('test')
        with self.login(user):
            self.get_check_200('view-needs-login')

    def test_reverse(self):
        self.assertEqual(self.reverse('view-200'), '/view/200/')

    def test_assertgoodview(self):
        self.assertGoodView('view-200')

    def test_assertnumqueries(self):
        with self.assertNumQueriesLessThan(1):
            self.get('view-needs-login')

    def test_assertnumqueries_data_1(self):
        with self.assertNumQueriesLessThan(2):
            self.get('view-data-1')

    def test_assertnumqueries_data_5(self):
        with self.assertNumQueriesLessThan(6):
            self.get('view-data-5')

    @unittest.expectedFailure
    def test_assertnumqueries_failure(self):
        if not DJANGO_16:
            return unittest.skip('Does not work before Django 1.6')

        with self.assertNumQueriesLessThan(1):
            self.get('view-data-5')

    def test_assertnumqueries_warning(self):
        if not DJANGO_16:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')

                with self.assertNumQueriesLessThan(1):
                    self.get('view-data-1')

                self.assertEqual(len(w), 1)
                self.assertTrue('skipped' in str(w[-1].message))
        else:
            return unittest.skip('Only useful for Django 1.6 and before')

    def test_assertincontext(self):
        response = self.get('view-context-with')
        self.assertTrue('testvalue' in response.context)

        self.assertInContext('testvalue')
        self.assertTrue(self.context['testvalue'], response.context['testvalue'])

    def test_get_context(self):
        response = self.get('view-context-with')
        self.assertTrue('testvalue' in response.context)
        value = self.get_context('testvalue')
        self.assertEqual(value, True)

    def test_assert_context(self):
        response = self.get('view-context-with')
        self.assertTrue('testvalue' in response.context)
        self.assertContext('testvalue', True)

    @unittest.expectedFailure
    def test_assertnotincontext(self):
        self.get('view-context-without')
        self.assertInContext('testvalue')

    def test_no_response(self):
        with self.assertRaises(NoPreviousResponse):
            self.assertInContext('testvalue')

    def test_get_is_ajax(self):
        response = self.get('view-is-ajax',
                            extra={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.response_200(response)

    def test_post_is_ajax(self):
        response = self.post('view-is-ajax',
                             data={'item': 1},
                             extra={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        self.response_200(response)

    def test_assertresponsecontains(self):
        self.get('view-contains')
        self.assertResponseContains('<p>Hello world</p>')
        self.assertResponseNotContains('<p>Hello Frank</p>')

    def test_assert_response_headers(self):
        self.get('view-headers')
        self.assertResponseHeaders({'Content-Type': 'text/plain'})
        self.assertResponseHeaders({'X-Custom': '1'})
        self.assertResponseHeaders({'X-Custom': '1', 'X-Non-Existent': None})
        self.assertResponseHeaders({'X-Non-Existent': None})


class TestPlusCBViewTests(CBVTestCase):

    def test_get(self):
        self.get(CBView)
        self.response_200()

    def test_post(self):
        data = {'testing': True}
        self.post(CBView, data=data)
        self.response_200()

    def test_get_check_200(self):
        self.get_check_200('cbview')

    def test_assert_good_view(self):
        self.assertGoodView('cbview')

    def test_login_required(self):
        self.assertLoginRequired('cbview-needs-login')

        # Make a user and login with our login context
        self.make_user('test')
        with self.login(username='test', password='password'):
            self.get_check_200('cbview-needs-login')


class TestPlusCBDataViewTests(CBVTestCase):
    """
    Provide usage examples for CBVTestCase
    """

    def setUp(self):
        self.data = Data.objects.create(name='RevSys')

    def test_get_request_attributes(self):
        """
        Ensure custom `request` attribute is seen at view
        """
        request = django.test.RequestFactory().get('/')
        # add custom attribute
        request.some_data = 5

        self.get(
            CBDataView,
            request=request,
            pk=self.data.pk,
        )
        # view copies `request.some_data` into context if present
        self.assertContext('some_data', 5)

    def test_get_override_view_template(self):
        """
        Ensure `initkwargs` overrides view attributes
        """
        request = django.test.RequestFactory().get('/')

        self.get(
            CBDataView,
            request=request,
            pk=self.data.pk,
        )
        self.assertTemplateUsed('test.html')  # default template

        # Use `initkwargs` to override view class "template_name" attribute
        self.get(
            CBDataView,
            request=request,
            pk=self.data.pk,
            initkwargs={
                'template_name': 'other.html',
            }
        )
        self.assertTemplateUsed('other.html')  # overridden template

    def test_post_request_attributes(self):
        """
        Ensure custom `request` attribute is seen at view
        """
        request = django.test.RequestFactory().post('/')
        # add custom attribute
        request.some_data = 5

        self.post(
            CBDataView,
            request=request,
            pk=self.data.pk,
            data={}  # no data, name is required so this will be invalid
        )
        # view copies `request.some_data` into context if present
        self.assertContext('some_data', 5)

    def test_post_override_view_template(self):
        """
        Ensure `initkwargs` overrides view attributes
        """
        request = django.test.RequestFactory().post('/')

        self.post(
            CBDataView,
            request=request,
            pk=self.data.pk,
            data={}  # no data, name is required so this will be invalid
        )
        self.assertTemplateUsed('test.html')  # default template

        # Use `initkwargs` to override view class "template_name" attribute
        self.post(
            CBDataView,
            request=request,
            pk=self.data.pk,
            initkwargs={
                'template_name': 'other.html',
            },
            data={}  # no data, name is required so this will be invalid
        )
        self.assertTemplateUsed('other.html')  # overridden template


class TestPlusCBTemplateViewTests(CBVTestCase):

    def test_get(self):
        response = self.get(CBTemplateView)
        self.assertEqual(response.status_code, 200)
        self.assertInContext('revsys')
        self.assertContext('revsys', 42)
        self.assertTemplateUsed(response, template_name='test.html')

    def test_get_new_template(self):
        template_name = 'other.html'
        response = self.get(CBTemplateView, initkwargs={'template_name': template_name})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name=template_name)


class TestPlusCBCustomMethodTests(CBVTestCase):

    def test_custom_method_with_value(self):
        special_value = 42
        instance = self.get_instance(CBView, initkwargs={'special_value': special_value})
        self.assertEqual(instance.special(), special_value)

    def test_custom_method_no_value(self):
        instance = self.get_instance(CBView)
        self.assertFalse(instance.special())


@unittest.skipUnless(DRF is True and DJANGO_18 is True, 'DRF is not installed.')
class TestAPITestCaseDRFInstalled(APITestCase):

    def test_post(self):
        data = {'testing': {'prop': 'value'}}
        self.post('view-json', data=data, extra={'format': 'json'})
        self.response_200()
