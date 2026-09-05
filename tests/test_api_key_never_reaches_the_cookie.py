#!/usr/bin/env python3
"""A visitor's OpenRouter key must not travel in their cookie.

`session['openrouter_api_key'] = api_key` put it there, and a Flask session cookie
is SIGNED, not encrypted: the signature stops the visitor editing it, and nothing
at all stops anyone reading it. The key -- which spends real money -- sat
base64-encoded in the browser's cookie jar and went back to the server on every
request, over plain HTTP, including requests for static files.

It is now held in this process, filed under the opaque session id the cookie
already carried.

The session id itself was assigned only by the `/demo` route. The interface the
documentation tells people to open is `/isee-ui`, which never passed through
there, so its visitors had no session: every analytics line read
`user_session=anonymous`, and the store above would have had nothing to file a key
under. It is assigned for every route now.
"""

import base64
import os
import zlib
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import app, demo

KEY = "sk-or-v1-example-key-for-this-test-only-0000000000"


def cookie_contents(client):
    """Everything the client would send back, decoded as far as it decodes.

    Flask signs the cookie and, when the payload is long enough, zlib-compresses it
    and marks that with a leading dot. Both are reversible by anyone holding the
    cookie -- which is the point: signing is not secrecy.

    The decompression step is here because without it this helper found nothing at
    all, in every case including the broken one, and the test below would have
    passed against a cookie that did contain the key. Verified by putting the key
    back into the session and watching it be found again.
    """
    parts = []
    for cookie in getattr(client, "_cookies", {}).values():
        for value in (cookie.values() if isinstance(cookie, dict) else [cookie]):
            raw = getattr(value, "value", str(value))
            parts.append(raw)
            for chunk in raw.split("."):
                if not chunk:
                    continue
                try:
                    decoded = base64.urlsafe_b64decode(chunk + "=" * (-len(chunk) % 4))
                except Exception:
                    continue
                parts.append(decoded.decode("utf-8", "replace"))
                try:
                    parts.append(zlib.decompress(decoded).decode("utf-8", "replace"))
                except Exception:
                    pass
    return chr(10).join(parts)  # chr(10), so no escape survives an edit


class TestTheHelperCanSeeIntoTheCookie(unittest.TestCase):
    """Guards the test below from passing for the wrong reason.

    The first version of cookie_contents could not decode a compressed session
    cookie, so it returned nothing and would have reported success no matter what
    the cookie held.
    """

    def test_a_value_in_the_session_is_found(self):
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["openrouter_api_key"] = KEY  # the state this file exists to forbid
        client.get("/isee-ui")

        self.assertIn(KEY, cookie_contents(client),
                      "the helper cannot see cookie contents, so the test that "
                      "relies on it proves nothing")


class TestTheKeyStaysOnTheServer(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app_module._session_api_keys.clear()

    def tearDown(self):
        app_module._session_api_keys.clear()

    def test_a_stored_key_is_not_in_the_cookie(self):
        with self.client.session_transaction() as sess:
            sess["session_id"] = "test-session"
        with app.test_request_context():
            from flask import session as flask_session
            flask_session["session_id"] = "test-session"
            self.assertTrue(app_module._remember_api_key(KEY))

        self.client.get("/isee-ui")

        self.assertNotIn(KEY, cookie_contents(self.client),
                         "the API key is readable in the session cookie")

    def test_the_key_is_recalled_for_the_session_that_set_it(self):
        with app.test_request_context():
            from flask import session as flask_session
            flask_session["session_id"] = "session-a"
            app_module._remember_api_key(KEY)
            self.assertEqual(app_module._recall_api_key(), KEY)

    def test_another_session_does_not_get_it(self):
        with app.test_request_context():
            from flask import session as flask_session
            flask_session["session_id"] = "session-a"
            app_module._remember_api_key(KEY)
        with app.test_request_context():
            from flask import session as flask_session
            flask_session["session_id"] = "session-b"
            self.assertIsNone(app_module._recall_api_key())

    def test_recall_outside_a_request_is_not_an_error(self):
        """A worker thread has no request context and calls into this code."""
        self.assertIsNone(app_module._recall_api_key())


class TestEverySessionHasAnIdentity(unittest.TestCase):

    def test_the_primary_interface_starts_a_session(self):
        client = app.test_client()

        client.get("/isee-ui")

        with client.session_transaction() as sess:
            self.assertIn("session_id", sess,
                          "/isee-ui left the visitor without a session, so their "
                          "API key would have had nowhere to go")

    def test_the_cookie_is_not_readable_by_page_scripts(self):
        self.assertTrue(app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(app.config["SESSION_COOKIE_SAMESITE"], "Lax")


if __name__ == "__main__":
    unittest.main()
