#!/usr/bin/env python3
"""A model call has to end, and a hopeless one must not be repeated.

Two independent limits meet here:

* `requests`' `timeout=` bounds the *silence* on a connection, not the length of
  the call. Measured against OpenRouter on 03.09.2026: a 77.8-second request
  never had a gap larger than 3.0 seconds between bytes, so a 10-second read
  timeout never fired — the gateway pads the connection while the model
  generates. A wall-clock deadline is therefore the only thing that can bound a
  call, and one straggler had held a run for 278 seconds without it.

* The API layer marks a failure retryable or not, and had always recorded that
  answer in the failure report — but the retry loop ignored it, so a request the
  server had already rejected as malformed was sent twice more with backoff.
"""

import asyncio
import os
import re
import sys
import time
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import model_api_integration as api


class FakeResponse:
    """Yields bytes on a schedule, so a deadline can be tested without a network."""

    def __init__(self, chunks, delay=0.0, status_code=200):
        self._chunks = chunks
        self._delay = delay
        self.status_code = status_code
        self.closed = False

    def iter_content(self, chunk_size=8192):
        for chunk in self._chunks:
            if self._delay:
                time.sleep(self._delay)
            yield chunk

    def close(self):
        self.closed = True


class TestReadDeadline(unittest.TestCase):
    def test_a_body_that_arrives_in_time_is_returned_whole(self):
        response = FakeResponse([b'{"a"', b': 1}'])

        body = api.OpenRouterClient._read_within_deadline(
            response, time.monotonic() + 10, "z-ai/glm")

        self.assertEqual(body, b'{"a": 1}')
        self.assertFalse(response.closed)

    def test_a_call_that_outlives_its_deadline_raises(self):
        response = FakeResponse([b"x"] * 20, delay=0.02)

        with self.assertRaises(api.APITimeoutError) as caught:
            api.OpenRouterClient._read_within_deadline(
                response, time.monotonic() - 1, "z-ai/glm")

        self.assertIn("deadline", str(caught.exception))

    def test_the_abandoned_connection_is_closed(self):
        response = FakeResponse([b"x"] * 5)

        with self.assertRaises(api.APITimeoutError):
            api.OpenRouterClient._read_within_deadline(
                response, time.monotonic() - 1, "z-ai/glm")

        self.assertTrue(response.closed)

    def test_a_deadline_failure_is_not_worth_retrying(self):
        # A model that has just spent the entire budget will not do better on a
        # second attempt; it will only spend it again.
        response = FakeResponse([b"x"] * 5)

        with self.assertRaises(api.APITimeoutError) as caught:
            api.OpenRouterClient._read_within_deadline(
                response, time.monotonic() - 1, "z-ai/glm")

        self.assertIs(caught.exception.retryable, False)
        self.assertEqual(caught.exception.model, "z-ai/glm")

    def test_an_empty_body_is_not_mistaken_for_a_timeout(self):
        body = api.OpenRouterClient._read_within_deadline(
            FakeResponse([]), time.monotonic() + 10)

        self.assertEqual(body, b"")


class TestEveryRequestIsBounded(unittest.TestCase):
    def test_no_request_goes_out_without_a_timeout(self):
        # Two call sites had none at all: a connection that never answers would
        # hang the calling thread, and with it the run, indefinitely.
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "model_api_integration.py"), encoding="utf-8") as fh:
            source = fh.read()

        calls = re.findall(r"requests\.(?:post|get)\((?:[^()]|\([^()]*\))*\)", source)
        self.assertTrue(calls, "no requests calls found — has the module moved?")

        without = [c for c in calls if "timeout" not in c]
        self.assertEqual(without, [], f"{len(without)} request(s) without a timeout")

    def test_the_deadline_is_longer_than_the_socket_timeout(self):
        # The other way round, the socket timeout would end calls the deadline was
        # meant to allow.
        self.assertGreater(api.CALL_DEADLINE_SECONDS, api.SOCKET_TIMEOUT_SECONDS)


class Boom(api.APIIntegrationError):
    pass


class TestRetryPolicy(unittest.IsolatedAsyncioTestCase):
    """The retry loop in the parallel engine."""

    def setUp(self):
        from main import ParallelExecutionEngine

        self.engine = ParallelExecutionEngine.__new__(ParallelExecutionEngine)
        self.engine.json_progress = False
        self.engine.completed_count = 0
        self.engine.failed_count = 0
        self.engine.total_combinations = 1
        self.engine.max_workers = 1

        # Only the provider lookup reaches into the application, and only for the
        # model's configured provider; an empty map falls through to the default.
        self.engine.isee_app = types.SimpleNamespace(model_configs={})

        import logging
        self.engine.logger = logging.getLogger("test_call_bounds")

    async def run_combination(self, error):
        """Drive one combination whose execution always raises `error`."""
        self.attempts = 0

        def explode(_combination):
            self.attempts += 1
            raise error

        self.engine._execute_combination_sync = explode
        self.engine.provider_semaphores = {"openrouter": asyncio.Semaphore(1)}

        combination = {"id": "c1", "model": "m", "template": "ins_analytical",
                       "domain": "dynamic:D", "query": "q"}
        return await self.engine.execute_single_combination(combination, True)

    async def test_a_retryable_failure_is_attempted_three_times(self):
        result = await self.run_combination(Boom("upstream hiccup", retryable=True))

        self.assertEqual(self.attempts, 3)
        self.assertEqual(result["attempts"], 3)

    async def test_a_failure_of_unknown_kind_is_still_attempted_three_times(self):
        # Anything that is not explicitly non-retryable keeps the old behaviour.
        result = await self.run_combination(RuntimeError("something odd"))

        self.assertEqual(self.attempts, 3)
        self.assertEqual(result["attempts"], 3)

    async def test_a_non_retryable_failure_is_attempted_once(self):
        result = await self.run_combination(
            Boom("HTTP 400: unsupported parameter", status_code=400, retryable=False))

        self.assertEqual(self.attempts, 1)
        self.assertEqual(result["attempts"], 1)
        self.assertIn("not retryable", result["error"])

    async def test_the_failure_record_carries_the_structured_detail(self):
        result = await self.run_combination(
            Boom("HTTP 400: unsupported parameter", status_code=400, retryable=False))

        self.assertEqual(result["error_detail"]["status_code"], 400)
        self.assertIs(result["error_detail"]["retryable"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
