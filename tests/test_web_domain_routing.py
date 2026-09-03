#!/usr/bin/env python3
"""Which command-line flag a domain gets on the way from the web UI to the engine.

The engine validates `--domain` and aborts the whole run on an unknown name;
`--dynamic-domain` accepts any name and uses it as context. The web UI generates
its domains per query through `/api/suggest-domains`, so most of them are, by
construction, not names the engine knows.

The routing used to hang off the `strategic_models` flag. The moment the UI began
sending an explicit model selection that flag went false, every generated domain
went out as a validated `--domain`, and the engine rejected the first one — the
run died before a single model call, and the interface still showed it completed.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_demo():
    """A bare ISEEWebDemo with a real domain manager and nothing else."""
    import logging

    from app import ISEEWebDemo
    from domain_manager import DomainManager, create_default_domains

    demo = ISEEWebDemo.__new__(ISEEWebDemo)
    demo.logger = logging.getLogger("test_web_domain_routing")
    demo.domain_manager = DomainManager()
    for domain in create_default_domains():
        demo.domain_manager.add_domain(domain)
    return demo


class TestKnownDomains(unittest.TestCase):
    def setUp(self):
        self.demo = make_demo()
        self.known = self.demo.domain_manager.list_domains()

    def test_the_engine_has_domains_to_recognise(self):
        self.assertTrue(self.known, "no default domains loaded")

    def test_a_domain_id_is_recognised(self):
        self.assertTrue(self.demo._is_known_domain(self.known[0].id))

    def test_a_domain_name_is_recognised_regardless_of_case(self):
        self.assertTrue(self.demo._is_known_domain(self.known[0].name.upper()))

    def test_a_generated_name_is_not_recognised(self):
        self.assertFalse(self.demo._is_known_domain("Energy Efficiency Engineering"))

    def test_empty_input_is_not_a_domain(self):
        self.assertFalse(self.demo._is_known_domain(""))
        self.assertFalse(self.demo._is_known_domain("   "))
        self.assertFalse(self.demo._is_known_domain(None))


class TestDomainFlags(unittest.TestCase):
    def setUp(self):
        self.demo = make_demo()
        self.known_name = self.demo.domain_manager.list_domains()[0].name

    def test_generated_domains_take_the_dynamic_flag(self):
        # This is the regression: these three are what /api/suggest-domains
        # produced for a real query, and all three used to abort the run.
        generated = ["Energy Efficiency Engineering",
                     "Sustainable IT Infrastructure",
                     "Facility Management and Operations"]

        flags = self.demo._domain_flags(generated)

        self.assertEqual(flags.count("--dynamic-domain"), 3)
        self.assertNotIn("--domain", flags)

    def test_a_known_domain_still_takes_the_validated_flag(self):
        flags = self.demo._domain_flags([self.known_name])

        self.assertEqual(flags, ["--domain", self.known_name])

    def test_an_explicit_dynamic_prefix_is_stripped_and_honoured(self):
        flags = self.demo._domain_flags([f"dynamic:{self.known_name}"])

        self.assertEqual(flags, ["--dynamic-domain", self.known_name])

    def test_a_mixed_list_routes_each_domain_on_its_own_merits(self):
        flags = self.demo._domain_flags([self.known_name, "Invented Domain"])

        self.assertEqual(flags, ["--domain", self.known_name,
                                 "--dynamic-domain", "Invented Domain"])

    def test_the_single_domain_parameter_is_routed_the_same_way(self):
        self.assertEqual(self.demo._domain_flags([], "Invented Domain"),
                         ["--dynamic-domain", "Invented Domain"])
        self.assertEqual(self.demo._domain_flags(None, self.known_name),
                         ["--domain", self.known_name])

    def test_a_list_wins_over_the_single_parameter(self):
        flags = self.demo._domain_flags(["Invented Domain"], self.known_name)

        self.assertEqual(flags, ["--dynamic-domain", "Invented Domain"])

    def test_no_domains_produce_no_flags(self):
        self.assertEqual(self.demo._domain_flags([], None), [])
        self.assertEqual(self.demo._domain_flags(None, None), [])

    def test_blank_entries_are_dropped_rather_than_passed_on(self):
        flags = self.demo._domain_flags(["", "dynamic:", "Invented Domain"])

        self.assertEqual(flags, ["--dynamic-domain", "Invented Domain"])

    def test_routing_does_not_depend_on_the_model_selection(self):
        # The decision must come from the domain alone. Nothing about models is
        # passed in here any more, which is the point — but pin it in the source
        # too, since the old coupling was invisible at this level.
        import inspect

        from app import ISEEWebDemo

        source = inspect.getsource(ISEEWebDemo.execute_isee_command)
        domain_section = source.split("Add selected domains")[1].split("Add cognitive")[0]
        code = [line for line in domain_section.splitlines()
                if not line.strip().startswith("#")]
        self.assertNotIn("strategic_models", "\n".join(code))


if __name__ == "__main__":
    unittest.main(verbosity=2)
