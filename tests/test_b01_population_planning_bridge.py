"""V1-064 logic witnesses: all numbers/premises below are supplied SCN, not defaults."""
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction as F
import unittest

from modules.B01.engine import create_population_plan, population_source_demo
from modules.B01.capability_contract import CapabilitySnapshot, EvidenceIdentity
from modules.B01.population_planning_bridge import (
    Allocation, Cell, Control, EligibleOriginInterval, EvidenceBinding, FixedSchedule, InterventionAlternative,
    JointWorld, LotValue, OptionValue, OriginLot, PlanningInputs, PopulationIdentity,
    PopulationPlanningError, RecordCorrespondence, ResourceEnvelope, ResourceSpec,
    ResourceValue, ResourceWindow, SourcePin, TargetControl, adapt_population_outputs,
    correspondence_report, exact, model_output_digest, load_population_contract,
)

PIN = "a" * 64
POP = PopulationIdentity("synthetic-closed-dwellings", "1", "DWELLING", "synthetic-region", "2028-01-01")


def witness(*, amounts=("10.5", "10.5"), eligible=("8", "4"), coefficients=("2", "3")):
    labour = ResourceSpec("labour", "OCCUPANCY", "FTE", "DWELLING", "crew", "R", "installer", "SCN-2028", "SCN-labour")
    cash = ResourceSpec("payment", "FLOW", "HUF", "DWELLING", "payments", "R", "programme", "SCN-2028-prices", "SCN-payment")
    options = (
        InterventionAlternative("parallel-package", "1", "cell", "BASE", "PACKAGE", "ELIGIBLE:package",
            "JOINT_INTERVENTION_ELIGIBILITY", "2028-01-01", "2030-01-01", (labour, cash),
            "SCN-complete-inventory", "SCN-parallel-endpoint", "COMPOSITE_ENDPOINT"),
        InterventionAlternative("alternative", "1", "cell", "BASE", "ALTERNATIVE", "ELIGIBLE:alternative",
            "JOINT_INTERVENTION_ELIGIBILITY", "2028-01-01", "2030-01-01", (labour,),
            "SCN-complete-inventory-no-other-demands", "SCN-alternative-endpoint"),
        InterventionAlternative("second-phase", "1", "cell", "PACKAGE", "LATER", "ELIGIBLE:second",
            "JOINT_INTERVENTION_ELIGIBILITY", "2028-01-01", "2030-01-01", (labour,),
            "SCN-complete-second-inventory", "SCN-second-endpoint"),
    )
    worlds = []
    for i, (amount, eligible_mass, coeff) in enumerate(zip(amounts, eligible, coefficients)):
        name = f"world-{i}"
        worlds.append(JointWorld(name, "SCN-joint", (LotValue(name, "root", amount, "DWELLING"),),
            tuple(OptionValue(name, o.option_id, eligible_mass, "DWELLING", tuple(
                ResourceValue(name, r.resource_id, coeff if r.resource_id == "labour" else "100") for r in o.resources),
                None if eligible_mass is None else (() if exact(eligible_mass) == 0 else (EligibleOriginInterval("origin", "0", eligible_mass),))) for o in options)))
    binding = EvidenceBinding("SCN", "SCN", "E3", "SCN-output", (SourcePin("SCN-artifact", PIN),),
        "complete synthetic closed cohort", "explicit Q only; no imputation", "SCN-joint", "finite joint scenario worlds; no probabilities",
        "SCN-qualified-input-receipt", ("STATE_DISTRIBUTION", "DISJOINT_PARTITION", *(o.eligible_claim for o in options),
            *(f"RESOURCE:{o.option_id}:{r.resource_id}" for o in options for r in o.resources)), scenario_ref="SCN-logic-witness")
    # A Q control permits differing jointly supplied represented mass without
    # pretending it reconciles to an observed point population control.
    return PlanningInputs("SCN-planning-set", "1", POP, "2028-01-01", "2030-01-01", "Europe/Budapest", "date-v1",
        "SCN-independent-capabilities", "1", ("BASE", "PACKAGE", "ALTERNATIVE", "LATER"), "SCN-disjoint-partition",
        "SCN-qualified-regional-scope", (TargetControl("control", ("atom",)),),
        (Cell("cell", "control", ("atom",), "R"),),
        (Control("control", POP, ("atom",), None, "SCN-artifact", PIN, "Q"),),
        (OriginLot("root", "origin", "cell", "BASE", ("root-alias",)),), options, tuple(worlds), binding)


def allocation(name="a", *, mass="5.25", source="root", offset="0", option="parallel-package",
               start="2028-03-01", effective="2028-06-01", windows=None):
    if windows is None:
        windows = (ResourceWindow("labour", "2028-02-01", "2028-08-01"),)
        if option == "parallel-package":
            windows += (ResourceWindow("payment", "2028-01-15"),)
    return Allocation(name, f"event-{name}", source, offset, mass, "DWELLING", option, f"child-{name}", start, effective, windows, "SCN-allocation")


def submit(session, *allocations, **overrides):
    return session.submit(replace(FixedSchedule("plan", "1", session.definition_digest, session.revision,
                                             "SCN-explicit-order", tuple(allocations)), **overrides))


def session(inputs=None):
    return create_population_plan(inputs=inputs or witness(), plan_id="plan", version="1")


def link(record="visit-1", household="household-1", dwelling="dwelling-1", *, context="REAL", **changes):
    identity = EvidenceIdentity(household, "site-1", "record-basis", context, "INDIVIDUAL_RECORD")
    result = RecordCorrespondence(record, household, dwelling, dwelling, "site-1", POP, "cell",
        "2028-01-01", "2029-01-01", "MANY_TO_MANY", "convenience correspondence; no inference", "mapping-evidence",
        "OBS" if context == "REAL" else "SCN", context, CapabilitySnapshot(identity, "2028-01-01"))
    return replace(result, **changes)


class PopulationPlanningBridgeTests(unittest.TestCase):
    def test_source_consumer_preserves_existing_p84_reader_and_q(self):
        from modules.B02.terminal_eligibility_population_inference import build_population_controls, current_repository_envelope
        out = population_source_demo()
        self.assertEqual(out["controls"], build_population_controls())
        self.assertEqual(out["terminal_eligibility"], current_repository_envelope())
        self.assertEqual((out["control_count"], out["represented_mass"], out["native_unit"], out["reference_date"]),
                         (40, 3389817, "DWELLING", "2022-10-01"))
        self.assertEqual(out["terminal_eligibility"].status, "Q")
        self.assertEqual((out["terminal_eligibility"].eligible_lower_dwellings,
                          out["terminal_eligibility"].eligible_upper_dwellings), (0, 3389817))
        self.assertIsNone(out["planning_state_distribution"])
        self.assertIsNone(out["intervention_eligible_mass"])
        self.assertEqual(len(out["artifact_sha256"]), 64)
        self.assertFalse(load_population_contract()["original_task_acceptance_changed"])

    def test_fixed_schedule_per_world_and_timing_conservation(self):
        s = session()
        submit(s, allocation())
        out = s.report(dates=("2028-01-01", "2028-03-01", "2028-05-31", "2028-06-01", "2028-08-01"))
        first, second = out["worlds"]
        self.assertEqual(first["outcomes"][0]["status"], "ADMISSIBLE")
        self.assertEqual(second["outcomes"][0]["status"], "ELIGIBILITY_OVERDRAW")
        self.assertEqual(first["outcomes"][0]["requested_mass"], second["outcomes"][0]["requested_mass"])
        self.assertIsNone(first["probability"])
        self.assertIsNone(out["overall_policy_verdict"])
        for stock in first["dated_stock"]:
            self.assertEqual(stock["total_mass"], F("10.5"))
            self.assertEqual(stock["conservation_residual"], 0)
        for stock in first["dated_stock"][:3]:
            self.assertEqual(stock["state_mass"][("cell", "BASE")], F("10.5"))
            self.assertEqual(stock["reserved_in_source"][("cell", "BASE")], F("5.25"))
            self.assertEqual(stock["state_mass"][("cell", "PACKAGE")], 0)
        milestone = first["dated_stock"][3]
        self.assertEqual(milestone["state_mass"][("cell", "BASE")], F("5.25"))
        self.assertEqual(milestone["state_mass"][("cell", "PACKAGE")], F("5.25"))
        self.assertEqual(milestone["reserved_in_source"][("cell", "BASE")], 0)
        self.assertEqual(second["dated_stock"][-1]["state_mass"][("cell", "PACKAGE")], 0)
        self.assertEqual(first["unique_origin_planning_mass"], F("5.25"))
        self.assertEqual(first["actual_household_completions"], 0)

    def test_repeat_phases_count_origin_union_not_throughput(self):
        s = session(witness(eligible=("10.5", "10.5")))
        submit(s, allocation(mass="3.5"), allocation("b", mass="3.5", source="child-a", option="second-phase",
              start="2028-06-01", effective="2028-07-01", windows=(ResourceWindow("labour", "2028-06-01", "2028-09-01"),)))
        world = s.report(dates=("2028-06-01", "2028-07-01"))["worlds"][0]
        self.assertEqual(world["transition_throughput"], 7)
        self.assertEqual(world["unique_origin_planning_mass"], F("3.5"))
        self.assertEqual(world["dated_stock"][0]["reserved_in_source"][("cell", "PACKAGE")], F("3.5"))
        self.assertEqual(world["dated_stock"][1]["state_mass"][("cell", "LATER")], F("3.5"))
        submit(s, allocation("c", mass="3.5", offset="3.5", option="alternative"))
        self.assertEqual(s.report()["worlds"][0]["unique_origin_planning_mass"], 7)

    def test_alternative_alias_retry_and_cumulative_overdraw(self):
        s = session()
        a = allocation(mass="3")
        submit(s, a)
        before = s.report()
        submit(s, a)
        self.assertEqual(s.report(), before)
        with self.assertRaisesRegex(PopulationPlanningError, "FIXED_SCHEDULE_OVERLAP"):
            submit(s, allocation("b", mass="3", source="root-alias", option="alternative"))
        self.assertEqual(s.report()["worlds"][0]["transition_throughput"], 3)
        with self.assertRaisesRegex(PopulationPlanningError, "alias"):
            submit(s, replace(a, allocation_id="another-id", child_lot_id="another-child"))
        with self.assertRaisesRegex(PopulationPlanningError, "REQUALIFICATION_REQUIRED"):
            submit(s, replace(a, mass="1"))
        submit(s, allocation("overdraw", mass="8", offset="3", option="alternative"))
        self.assertEqual(s.report()["worlds"][0]["outcomes"][-1]["status"], "OVERDRAW")

    def test_stale_revision_mutation_and_atomic_preflight(self):
        s = session()
        old = s.definition_digest
        submit(s, allocation(mass="3"))
        before = s.report()
        with self.assertRaisesRegex(PopulationPlanningError, "STALE_REVISION"):
            submit(s, allocation("b"), expected_revision=0)
        with self.assertRaisesRegex(PopulationPlanningError, "REQUALIFICATION_REQUIRED"):
            submit(s, allocation("b"), definition_digest="b" * 64)
        with self.assertRaisesRegex(PopulationPlanningError, "native mass unit"):
            submit(s, allocation("b", mass="1", offset="3"), replace(allocation("c"), unit="HOUSEHOLD"))
        self.assertEqual(s.report(), before)
        before["worlds"][0]["outcomes"][0]["status"] = "OBS"
        self.assertEqual(s.report()["worlds"][0]["outcomes"][0]["status"], "ADMISSIBLE")
        self.assertEqual(s.definition_digest, old)

    def test_unknown_zero_fraction_and_exact_arithmetic(self):
        for invalid in (True, False, float("nan"), float("inf"), 1.0, "NaN", "Infinity", "-0.1"):
            with self.subTest(value=invalid), self.assertRaises(PopulationPlanningError):
                exact(invalid)
        self.assertEqual(exact(0), 0)
        self.assertIsNone(exact(None, unknown=True))
        for amount, expected in ((None, "UNKNOWN"), ("0", "OVERDRAW")):
            s = session(witness(amounts=(amount, "10.5"), eligible=("0" if amount == "0" else "8", "4")))
            submit(s, allocation())
            self.assertEqual(s.report()["worlds"][0]["outcomes"][0]["status"], expected)
        with localcontext() as ctx:
            ctx.prec = 2
            s = session()
            submit(s, allocation(mass=Decimal("0.123456789")))
            self.assertEqual(s.report()["worlds"][0]["transition_throughput"], F("0.123456789"))

    def test_control_reconciliation_partial_scope_and_no_uniform_imputation(self):
        inp = witness()
        unchecked = adapt_population_outputs(inp)[0]
        self.assertEqual(unchecked["status"], "Q_CONTROL")
        self.assertTrue(unchecked["control_missing"])
        self.assertFalse(unchecked["represented_mass_missing"])
        self.assertIsNone(unchecked["reconciliation_residual"])
        missing_stock = adapt_population_outputs(witness(amounts=(None, "10.5")))[0]
        self.assertEqual(missing_stock["status"], "Q")
        self.assertTrue(missing_stock["represented_mass_missing"])
        control = replace(inp.controls[0], mass="10.5", evidence_status="SCN")
        inp = replace(inp, controls=(control,))
        self.assertEqual(adapt_population_outputs(inp)[0]["status"], "EXACT")
        bad = replace(inp, controls=(replace(control, mass="10"),))
        with self.assertRaisesRegex(PopulationPlanningError, "reconciliation"):
            session(bad)
        partial = replace(inp, controls=(replace(control, mass="20", scope_atoms=("atom", "uncovered-region")),),
                          target_controls=(TargetControl("control", ("atom", "uncovered-region")),))
        report = adapt_population_outputs(partial)[0]
        self.assertEqual(report["uncovered_atoms"], ("uncovered-region",))
        self.assertEqual(report["represented_mass"], F("10.5"))
        self.assertEqual(report["status"], "PARTIAL")
        with self.assertRaisesRegex(PopulationPlanningError, "aliased cell"):
            session(replace(inp, cells=inp.cells + (replace(inp.cells[0], cell_id="alias"),)))
        with self.assertRaisesRegex(PopulationPlanningError, "outside declared target"):
            session(replace(inp, controls=inp.controls + (replace(control, control_id="duplicate"),)))
        with self.assertRaisesRegex(PopulationPlanningError, "overlapping target"):
            session(replace(inp, target_controls=inp.target_controls + (TargetControl("duplicate", ("atom",)),)))

    def test_vintage_units_and_reclassification_need_new_qualification(self):
        inp = witness()
        for unit in ("HOUSEHOLD", "BUILDING", "SAMPLE_WEIGHT"):
            with self.subTest(unit=unit), self.assertRaises(PopulationPlanningError):
                session(replace(inp, population=replace(POP, native_unit=unit)))
        historic = replace(inp.controls[0], population=replace(POP, reference_date="2022-10-01"))
        with self.assertRaisesRegex(PopulationPlanningError, "vintage"):
            session(replace(inp, controls=(historic,)))
        rolled = replace(inp, controls=(historic,), roll_forward_ref="explicit-SCN-closed-cohort-2028-premise")
        self.assertEqual(adapt_population_outputs(rolled)[0]["status"], "HISTORICAL_CONTEXT")
        old = session(inp)
        changed = session(replace(inp, state_version="2"))
        with self.assertRaisesRegex(PopulationPlanningError, "REQUALIFICATION_REQUIRED"):
            submit(changed, allocation(), definition_digest=old.definition_digest)
        changed = session(replace(inp, calendar_version="2"))
        with self.assertRaises(PopulationPlanningError):
            submit(changed, allocation(), definition_digest=old.definition_digest)

    def test_joint_world_alignment_and_no_equal_probability(self):
        inp = witness()
        world = inp.worlds[0]
        with self.assertRaisesRegex(PopulationPlanningError, "world identity"):
            session(replace(inp, worlds=(replace(world, lots=(replace(world.lots[0], world_id="foreign"),)), inp.worlds[1])))
        option = world.options[0]
        changed = replace(option, coefficients=(replace(option.coefficients[0], world_id="foreign"), option.coefficients[1]))
        with self.assertRaisesRegex(PopulationPlanningError, "unrelated realization"):
            session(replace(inp, worlds=(replace(world, options=(changed, *world.options[1:])), inp.worlds[1])))
        with self.assertRaisesRegex(PopulationPlanningError, "semantic universe"):
            session(replace(inp, worlds=(replace(world, options=world.options[:1]), inp.worlds[1])))
        with self.assertRaisesRegex(PopulationPlanningError, "probabilities"):
            session(replace(inp, worlds=(replace(world, probability="0.5"), inp.worlds[1])))
        probability = replace(inp, worlds=(replace(world, probability="0.2"), replace(inp.worlds[1], probability="0.8")))
        result = session(probability).report()
        self.assertEqual(result["worlds"][0]["probability"], F("0.2"))
        self.assertIsNone(result["overall_policy_verdict"])

    def test_resources_use_native_denominator_independent_dates_and_world_values(self):
        s = session(witness(eligible=("10.5", "10.5")))
        submit(s, allocation(mass="2"))
        first, second = s.report()["worlds"]
        labour, cash = first["resources"]
        self.assertEqual(labour["concurrent_peak"], 4)
        self.assertEqual(second["resources"][0]["concurrent_peak"], 6)
        self.assertEqual(labour["occupancy_segments"][0]["end"], "2028-08-01")
        self.assertEqual(cash["events"][0]["start"], "2028-01-15")
        self.assertEqual(cash["annual_flows"], {2028: F(200)})
        self.assertEqual(first["envelope_coverage"][0]["status"], "Q_UNCOVERED_RESOURCE_DATES")
        altered = session(witness(eligible=("10.5", "10.5")))
        submit(altered, allocation(mass="2", effective="2028-07-01"))
        self.assertEqual(first["resources"], altered.report()["worlds"][0]["resources"])

    def test_concurrent_peak_is_not_annual_flow_and_end_is_exclusive(self):
        s = session(witness(eligible=("10.5", "10.5"), coefficients=("1", "1")))
        submit(s, allocation(mass="2", windows=(ResourceWindow("labour", "2028-02-01", "2028-04-01"), ResourceWindow("payment", "2028-01-15"))),
               allocation("b", mass="3", offset="2", windows=(ResourceWindow("labour", "2028-04-01", "2028-06-01"), ResourceWindow("payment", "2029-01-15"))))
        labour, cash = s.report()["worlds"][0]["resources"]
        self.assertEqual(labour["concurrent_peak"], 3)
        self.assertEqual(cash["annual_flows"], {2028: F(200), 2029: F(300)})
        self.assertEqual([s["quantity"] for s in labour["occupancy_segments"]], [2, 3])

    def test_envelope_shortfall_does_not_post_mass_or_resources(self):
        inp = witness(eligible=("10.5", "10.5"))
        spec = inp.options[0].resources[0]
        env = ResourceEnvelope("crew-cap", spec, "2028-01-01", "2030-01-01", "3", "SCN-cap", "world-0")
        inp = replace(inp, worlds=(replace(inp.worlds[0], envelopes=(env,)), inp.worlds[1]),
                      binding=replace(inp.binding, qualified_claims=(*inp.binding.qualified_claims, f"CAPACITY:{env.envelope_id}")))
        s = session(inp)
        submit(s, allocation(mass="2"))
        out = s.report()["worlds"][0]
        self.assertEqual(out["outcomes"][0]["status"], "RESOURCE_EXCESS")
        self.assertEqual(out["outcomes"][0]["trial_envelope_checks"][0]["used_or_peak"], 4)
        self.assertEqual(out["transition_throughput"], 0)
        self.assertEqual(out["resources"], ())
        self.assertEqual(out["dated_stock"][0]["total_mass"], F("10.5"))
        bad_env = replace(env, spec=replace(spec, actor="other"))
        with self.assertRaisesRegex(PopulationPlanningError, "unit/actor/region/basis"):
            session(replace(inp, worlds=(replace(inp.worlds[0], envelopes=(bad_env,)), inp.worlds[1])))

    def test_q_envelope_for_unchosen_pool_is_not_an_allocation_prerequisite(self):
        inp = witness()
        unused_spec = replace(inp.options[1].resources[0], pool="unused-alternative-pool")
        unused_option = replace(inp.options[1], resources=(unused_spec,))
        env = ResourceEnvelope("unused-pool-Q", unused_spec, "2028-01-01", "2030-01-01", None,
                               "SCN-unused-capacity-source", "world-0")
        inp = replace(inp, options=(inp.options[0], unused_option, inp.options[2]),
            worlds=(replace(inp.worlds[0], envelopes=(env,)), inp.worlds[1]),
            binding=replace(inp.binding, qualified_claims=(*inp.binding.qualified_claims, "CAPACITY:unused-pool-Q")))
        s = session(inp)
        submit(s, allocation(mass="2"))
        world = s.report()["worlds"][0]
        outcome = world["outcomes"][0]
        self.assertEqual(outcome["status"], "ADMISSIBLE")
        self.assertEqual(outcome["resource_status"], "REQUIREMENTS_KNOWN_CAPACITY_SCOPE_INCOMPLETE")
        check = outcome["trial_envelope_checks"][0]
        self.assertEqual(check["status"], "NOT_APPLICABLE")
        self.assertFalse(check["applicable"])
        self.assertIsNone(check["ceiling"])
        self.assertEqual(check["evidence_ref"], env.evidence_ref)
        self.assertTrue(all(c["status"] == "Q_UNCOVERED_RESOURCE_DATES" for c in world["envelope_coverage"]))
        self.assertEqual(world["transition_throughput"], 2)

    def test_q_envelope_nonoverlapping_dates_respect_flow_and_half_open_occupancy(self):
        for resource_id, start, end in (
            ("labour", "2028-01-01", "2028-02-01"),
            ("labour", "2028-08-01", "2028-09-01"),
            ("payment", "2028-01-01", "2028-01-15"),
            ("payment", "2028-01-16", "2028-02-01"),
        ):
            with self.subTest(resource=resource_id, start=start):
                inp = witness()
                spec = next(r for r in inp.options[0].resources if r.resource_id == resource_id)
                env = ResourceEnvelope("outside-dates-Q", spec, start, end, None, "SCN-outside-date-source", "world-0")
                inp = replace(inp, worlds=(replace(inp.worlds[0], envelopes=(env,)), inp.worlds[1]),
                    binding=replace(inp.binding, qualified_claims=(*inp.binding.qualified_claims, "CAPACITY:outside-dates-Q")))
                s = session(inp)
                submit(s, allocation(mass="2"))
                world = s.report()["worlds"][0]
                self.assertEqual(world["outcomes"][0]["status"], "ADMISSIBLE")
                check = world["envelope_checks"][0]
                self.assertEqual(check["status"], "NOT_APPLICABLE")
                self.assertFalse(check["applicable"])
                self.assertIsNone(check["ceiling"])
                self.assertEqual(check["evidence_ref"], env.evidence_ref)
                self.assertEqual(check["fit_basis"], "NO_MATCHING_RESOURCE_DATE_DEMAND")
                self.assertTrue(all(c["status"] == "Q_UNCOVERED_RESOURCE_DATES" for c in world["envelope_coverage"]))

    def test_zero_demand_fits_q_nonnegative_capacity_without_resolving_the_ceiling(self):
        for resource_id in ("labour", "payment"):
            with self.subTest(resource=resource_id):
                inp = witness()
                world = inp.worlds[0]
                option = world.options[0]
                option = replace(option, coefficients=tuple(replace(v, per_unit_quantity="0")
                    if v.resource_id == resource_id else v for v in option.coefficients))
                spec = next(r for r in inp.options[0].resources if r.resource_id == resource_id)
                env = ResourceEnvelope("zero-demand-Q", spec, "2028-01-01", "2030-01-01", None,
                                       "SCN-unresolved-capacity-source", "world-0")
                inp = replace(inp, worlds=(replace(world, options=(option, *world.options[1:]), envelopes=(env,)), inp.worlds[1]),
                    binding=replace(inp.binding, qualified_claims=(*inp.binding.qualified_claims, "CAPACITY:zero-demand-Q")))
                s = session(inp)
                submit(s, allocation(mass="2"))
                world = s.report()["worlds"][0]
                self.assertEqual(world["outcomes"][0]["status"], "ADMISSIBLE")
                for check in (world["outcomes"][0]["trial_envelope_checks"][0], world["envelope_checks"][0],
                              world["fixed_schedule_envelope_checks"][0]):
                    self.assertEqual(check["status"], "PASS")
                    self.assertTrue(check["applicable"])
                    self.assertEqual(check["used_or_peak"], 0)
                    self.assertIsNone(check["ceiling"])
                    self.assertEqual(check["evidence_ref"], env.evidence_ref)
                    self.assertEqual(check["fit_basis"], "KNOWN_ZERO_DEMAND_NONNEGATIVE_CAPACITY_DOMAIN")
                # The other resource still has no qualified capacity envelope.
                self.assertIn("Q_UNCOVERED_RESOURCE_DATES", [c["status"] for c in world["envelope_coverage"]])

    def test_applicable_unknown_positive_and_excess_demand_keep_their_boundaries(self):
        for resource_id in ("labour", "payment"):
            for coefficient, ceiling, outcome_status, check_status in (
                (None, None, "UNKNOWN", "Q"),
                (None, "0", "UNKNOWN", "Q"),
                ("1", None, "UNKNOWN", "Q"),
                ("1", "0", "RESOURCE_EXCESS", "FAIL"),
                ("1", "2", "ADMISSIBLE", "PASS"),
            ):
                with self.subTest(resource=resource_id, coefficient=coefficient, ceiling=ceiling):
                    inp = witness()
                    world = inp.worlds[0]
                    option = replace(world.options[0], coefficients=tuple(replace(v, per_unit_quantity=coefficient)
                        if v.resource_id == resource_id else v for v in world.options[0].coefficients))
                    spec = next(r for r in inp.options[0].resources if r.resource_id == resource_id)
                    env = ResourceEnvelope("applicable-capacity", spec, "2028-01-01", "2030-01-01", ceiling,
                                           "SCN-applicable-capacity-source", "world-0")
                    inp = replace(inp, worlds=(replace(world, options=(option, *world.options[1:]), envelopes=(env,)), inp.worlds[1]),
                        binding=replace(inp.binding, qualified_claims=(*inp.binding.qualified_claims, "CAPACITY:applicable-capacity")))
                    s = session(inp)
                    submit(s, allocation(mass="2"))
                    world = s.report()["worlds"][0]
                    outcome = world["outcomes"][0]
                    self.assertEqual(outcome["status"], outcome_status)
                    check = outcome["trial_envelope_checks"][0]
                    self.assertEqual(check["status"], check_status)
                    self.assertTrue(check["applicable"])
                    self.assertEqual(check["ceiling"], None if ceiling is None else F(ceiling))
                    self.assertEqual(check["evidence_ref"], env.evidence_ref)
                    if outcome_status != "ADMISSIBLE":
                        self.assertEqual(world["transition_throughput"], 0)
                        self.assertEqual(world["resources"], ())
                    if coefficient is None:
                        self.assertIsNone(check["used_or_peak"])

    def test_resource_missingness_and_denominator_are_not_repaired(self):
        inp = witness()
        world = inp.worlds[0]
        option = world.options[0]
        option = replace(option, coefficients=(replace(option.coefficients[0], per_unit_quantity=None), option.coefficients[1]))
        s = session(replace(inp, worlds=(replace(world, options=(option, *world.options[1:])), inp.worlds[1])))
        submit(s, allocation(mass="1"))
        out = s.report()["worlds"][0]
        self.assertEqual(out["outcomes"][0]["status"], "UNKNOWN")
        self.assertIsNone(out["outcomes"][0]["requested_resources"][0]["quantity"])
        self.assertEqual(out["resources"], ())
        bad = replace(inp.options[0], resources=(replace(inp.options[0].resources[0], denominator_unit="HOUSEHOLD"), inp.options[0].resources[1]))
        with self.assertRaisesRegex(PopulationPlanningError, "denominator"):
            session(replace(inp, options=(bad, *inp.options[1:])))
        with self.assertRaisesRegex(PopulationPlanningError, "resource window"):
            submit(session(), allocation(windows=()))

    def test_screening_mean_finance_status_and_control_are_not_eligibility(self):
        inp = witness()
        for meaning in ("SCREENING_CONTROL", "AVERAGE_CASH_SURPLUS", "INDIVIDUAL_PERMISSION"):
            with self.subTest(meaning=meaning), self.assertRaisesRegex(PopulationPlanningError, "eligibility"):
                session(replace(inp, options=(replace(inp.options[0], eligibility_meaning=meaning), *inp.options[1:])))
        with self.assertRaisesRegex(PopulationPlanningError, "CONTROL/Q"):
            session(replace(inp, binding=replace(inp.binding, mode="CONTROL")))
        with self.assertRaisesRegex(PopulationPlanningError, "claim-specific"):
            session(replace(inp, binding=replace(inp.binding, qualified_claims=("STATE_DISTRIBUTION",))))
        with self.assertRaisesRegex(PopulationPlanningError, "observed implementation"):
            submit(session(), replace(allocation(), planning_status="IMPLEMENTED"))

    def test_admitted_e2_output_needs_receipt_and_hash_but_no_full_record_census(self):
        inp = replace(witness(), central_world_id="world-0")
        binding = replace(inp.binding, mode="ADMITTED_ESTIMATE", evidence_status="DER", evidence_tier="E2",
            model_id="externally-admitted-model", model_version="1", output_sha256=model_output_digest(inp),
            selection_weighting_ref="qualified-frame-and-calibration", validation_diagnostics_ref="held-out-diagnostics",
            structural_sensitivity_ref="dependence-sensitivity", central_definition_id="one-canonical-base",
            validation_debt=("exact primary measurements pending; qualified E2 supports declared aggregate scope",))
        inp = replace(inp, binding=binding)
        s = session(inp)
        submit(s, allocation(mass="1"))
        out = s.report()
        self.assertEqual(out["binding"].evidence_tier, "E2")
        self.assertEqual(out["correspondence"]["counts"]["actual"]["records"], 0)
        self.assertEqual(out["worlds"][0]["outcomes"][0]["status"], "ADMISSIBLE")
        with self.assertRaisesRegex(PopulationPlanningError, "validation debt"):
            session(replace(inp, binding=replace(binding, validation_debt=())))
        with self.assertRaisesRegex(PopulationPlanningError, "digest mismatch"):
            session(replace(inp, state_version="2"))
        with self.assertRaisesRegex(PopulationPlanningError, "validation_diagnostics"):
            session(replace(inp, binding=replace(binding, validation_diagnostics_ref="")))

    def test_correspondence_cardinality_and_actual_evaluator_are_separate(self):
        s = session()
        before = s.report()["worlds"]
        links = (link(), link("visit-2"), link("visit-3", household="household-2"),
                 link("visit-4", dwelling="dwelling-2"), link("scenario-visit", context="SCN"))
        out = s.report(records=links)
        counts = out["correspondence"]["counts"]
        self.assertEqual(counts["actual"], {"records": 4, "households": 2, "dwellings": 2, "population_units": 2, "sites": 1})
        self.assertEqual(counts["scenario"]["records"], 1)
        self.assertEqual(out["worlds"], before)
        self.assertEqual(out["correspondence"]["population_mass_adjustment"], 0)
        self.assertEqual(out["correspondence"]["record_assessments"][0][1].complete_triple.status, "UNKNOWN")
        self.assertFalse(out["correspondence"]["record_assessments"][0][1].selected_or_funded)
        self.assertEqual(correspondence_report(witness(), (link(), link()), "2028-01-01")["counts"]["actual"]["records"], 1)

    def test_ambiguous_and_stale_membership_and_no_population_snapshot(self):
        inp = witness()
        inp = replace(inp, cells=inp.cells + (Cell("other", "control", ("other-atom",), "R"),))
        result = correspondence_report(inp, (link(), link("other-record", cell_id="other")), "2028-01-01")
        self.assertEqual(result["counts"]["actual"]["records"], 0)
        self.assertTrue(all(reason == "AMBIGUOUS_MEMBERSHIP" for _, reason in result["exceptions"]))
        stale = link(snapshot=None, valid_until="2028-01-01", valid_from="2027-01-01")
        result = session().report(records=(stale,))
        self.assertEqual(result["correspondence"]["exceptions"], (("visit-1", "STALE_MEMBERSHIP"),))
        with self.assertRaisesRegex(PopulationPlanningError, "CapabilitySnapshot"):
            session().report(records=(link(snapshot=witness().cells[0]),))
        population_identity = replace(link().snapshot.identity, evidence_scope="POPULATION")
        with self.assertRaisesRegex(ValueError, "population evidence"):
            session().report(records=(link(snapshot=CapabilitySnapshot(population_identity, "2028-01-01")),))

    def test_failed_world_cannot_select_an_overlapping_fallback_alternative(self):
        s = session(witness(eligible=("1", "4")))
        submit(s, allocation(mass="3"))
        before = s.report()
        self.assertEqual(before["worlds"][0]["outcomes"][0]["status"], "ELIGIBILITY_OVERDRAW")
        self.assertEqual(before["worlds"][0]["transition_throughput"], 0)
        with self.assertRaisesRegex(PopulationPlanningError, "world-specific fallback"):
            submit(s, allocation("fallback", mass="1", source="root-alias", option="alternative"))
        self.assertEqual(s.report(), before)
        fresh = session()
        with self.assertRaisesRegex(PopulationPlanningError, "FIXED_SCHEDULE_OVERLAP"):
            submit(fresh, allocation(mass="3"), allocation("fallback", mass="1", option="alternative"))
        self.assertEqual(fresh.revision, 0)
        self.assertEqual(fresh.report()["fixed_schedule_allocations"], ())


    def test_whole_missing_control_cannot_shrink_declared_national_universe(self):
        regional = witness()
        national = replace(regional, target_scope_id="SCN-qualified-national-scope",
            target_controls=regional.target_controls + (TargetControl("other-control", ("other-region",)),))
        report = adapt_population_outputs(national)
        missing = [r for r in report if r["control_id"] == "other-control"]
        self.assertEqual(len(missing), 2)
        self.assertTrue(all(r["status"] == "Q_CONTROL_NOT_SUPPLIED" for r in missing))
        self.assertTrue(all(r["control_row_missing"] for r in missing))
        self.assertEqual(missing[0]["uncovered_atoms"], ("other-region",))
        # Declaring a bounded regional target does not require national inputs.
        s = session(regional)
        submit(s, allocation(mass="1"))
        self.assertEqual(s.report()["worlds"][0]["outcomes"][0]["status"], "ADMISSIBLE")
        self.assertEqual(s.report()["target_scope_id"], "SCN-qualified-regional-scope")
        self.assertTrue(all(not r["uncovered_atoms"] for r in s.report()["control_reconciliation"]))
        with self.assertRaisesRegex(PopulationPlanningError, "target control universe"):
            session(replace(regional, target_controls=()))


    def test_same_eligible_marginals_different_joint_sets_are_not_exchangeable(self):
        inp = witness(eligible=("4", "4"), coefficients=("1", "1"))
        # Both worlds have the same per-option eligible scalar. In world-0 the
        # alternatives overlap completely; in world-1 they qualify disjoint mass.
        world = inp.worlds[1]
        alternative = replace(world.options[1], eligible_origins=(EligibleOriginInterval("origin", "4", "8"),))
        inp = replace(inp, worlds=(inp.worlds[0], replace(world, options=(world.options[0], alternative, world.options[2]))))
        s = session(inp)
        submit(s, allocation(mass="4"), allocation("b", mass="4", offset="4", option="alternative"))
        first, second = s.report()["worlds"]
        self.assertEqual(first["outcomes"][1]["status"], "ELIGIBILITY_SCOPE_MISMATCH")
        self.assertEqual(second["outcomes"][1]["status"], "ADMISSIBLE")
        self.assertEqual(first["unique_origin_planning_mass"], 4)
        self.assertEqual(second["unique_origin_planning_mass"], 8)
        self.assertEqual(first["outcomes"][1]["requested_mass"], second["outcomes"][1]["requested_mass"])

    def test_scalar_eligibility_does_not_supply_missing_joint_membership(self):
        inp = witness()
        world = inp.worlds[0]
        option = replace(world.options[0], eligible_origins=None)
        s = session(replace(inp, worlds=(replace(world, options=(option, *world.options[1:])), inp.worlds[1])))
        submit(s, allocation(mass="2"))
        out = s.report()["worlds"][0]
        self.assertEqual(out["outcomes"][0]["status"], "UNKNOWN")
        self.assertEqual(out["transition_throughput"], 0)
        self.assertEqual(out["resources"], ())

    def test_joint_eligibility_coordinate_validation_and_child_root_offset(self):
        inp = witness(eligible=("4", "4"))
        world = inp.worlds[0]
        for intervals, error in (
            ((EligibleOriginInterval("origin", "0", "3"),), "union differs"),
            ((EligibleOriginInterval("origin", "0", "3"), EligibleOriginInterval("origin", "2", "3")), "overlapping"),
            ((EligibleOriginInterval("origin", "9", "13"),), "exceeds"),
            ((EligibleOriginInterval("wrong-origin", "0", "4"),), "unknown eligible origin"),
        ):
            changed = replace(world.options[0], eligible_origins=intervals)
            with self.subTest(error=error), self.assertRaisesRegex(PopulationPlanningError, error):
                session(replace(inp, worlds=(replace(world, options=(changed, *world.options[1:])), inp.worlds[1])))
        # First phase selects root [2, 6). Its child offset 1 is root coordinate 3.
        inp = witness(eligible=("8", "8"))
        worlds = []
        for world in inp.worlds:
            changed = replace(world.options[2], eligible_mass="2",
                eligible_origins=(EligibleOriginInterval("origin", "3", "5"),))
            worlds.append(replace(world, options=(*world.options[:2], changed)))
        s = session(replace(inp, worlds=tuple(worlds)))
        submit(s, allocation(mass="4", offset="2"), allocation("b", source="child-a", mass="2", offset="1",
               option="second-phase", start="2028-06-01", effective="2028-07-01"))
        self.assertEqual(s.report()["worlds"][0]["outcomes"][1]["status"], "ADMISSIBLE")
        self.assertEqual(s.report()["worlds"][0]["unique_origin_planning_mass"], 4)
        self.assertEqual(s.report()["worlds"][0]["transition_throughput"], 6)


    def test_partial_envelope_exposes_uncovered_dates_without_fabricating_capacity(self):
        inp = witness()
        spec = inp.options[0].resources[0]
        env = ResourceEnvelope("partial-crew", spec, "2028-02-01", "2028-04-01", "20", "SCN-partial", "world-0")
        inp = replace(inp, worlds=(replace(inp.worlds[0], envelopes=(env,)), inp.worlds[1]),
                      binding=replace(inp.binding, qualified_claims=(*inp.binding.qualified_claims, f"CAPACITY:{env.envelope_id}")))
        s = session(inp)
        submit(s, allocation(mass="2"))
        out = s.report()["worlds"][0]
        self.assertEqual(out["envelope_checks"][0]["status"], "PASS")
        self.assertEqual(out["envelope_checks"][0]["valid_until"], "2028-04-01")
        self.assertEqual(out["envelope_coverage"][0]["status"], "Q_UNCOVERED_RESOURCE_DATES")
        self.assertEqual(out["outcomes"][0]["population_status"], "ADMISSIBLE")
        self.assertEqual(out["outcomes"][0]["resource_status"], "REQUIREMENTS_KNOWN_CAPACITY_SCOPE_INCOMPLETE")
        self.assertEqual(out["resources"][0]["occupancy_segments"][0]["end"], "2028-08-01")

    def test_source_identity_cardinality_cannot_alias_dwelling_household_or_building(self):
        with self.assertRaisesRegex(PopulationPlanningError, "dwelling population-unit"):
            session().report(records=(link(population_unit_id="different-source-unit"),))
        household_population = replace(POP, native_unit="HOUSEHOLD")
        household_link = link(population=household_population, population_unit_id="other-household")
        with self.assertRaisesRegex(PopulationPlanningError, "household population-unit"):
            correspondence_report(replace(witness(), population=household_population), (household_link,), "2028-01-01")
        building_population = replace(POP, native_unit="BUILDING")
        # Two qualified building identities may share a site; no site=building
        # or dwelling=building substitution is made by the bridge.
        links = (link(population=building_population, population_unit_id="building-1"),
                 link("visit-2", dwelling="dwelling-2", population=building_population, population_unit_id="building-2"))
        report = correspondence_report(replace(witness(), population=building_population), links, "2028-01-01")
        self.assertEqual(report["counts"]["actual"]["population_units"], 2)
        self.assertEqual(report["counts"]["actual"]["sites"], 1)
        self.assertEqual(report["counts"]["actual"]["dwellings"], 2)

    def test_world_stock_failure_keeps_same_quantity_and_no_partial_resources(self):
        s = session(witness(amounts=("10.5", "4"), eligible=("8", "4")))
        submit(s, allocation())
        first, second = s.report()["worlds"]
        self.assertEqual(first["outcomes"][0]["status"], "ADMISSIBLE")
        self.assertEqual(second["outcomes"][0]["status"], "OVERDRAW")
        self.assertEqual(second["outcomes"][0]["requested_mass"], F("5.25"))
        self.assertEqual(second["outcomes"][0]["requested_resources"][0]["quantity"], F("15.75"))
        self.assertEqual(second["resources"], ())
        self.assertEqual(second["fixed_schedule_requirements"][0]["concurrent_peak"], F("15.75"))
        self.assertEqual(s.report()["fixed_schedule_allocations"], (allocation(),))
        self.assertEqual(second["dated_stock"][0]["total_mass"], 4)
        with self.assertRaisesRegex(PopulationPlanningError, "eligible mass exceeds"):
            session(witness(amounts=("1", "10.5")))


    def test_predecessor_not_effective_never_creates_intermediate_completion(self):
        s = session(witness(eligible=("10.5", "10.5")))
        submit(s, allocation(mass="2"), allocation("b", source="child-a", mass="2", option="second-phase",
               start="2028-05-01", effective="2028-07-01"))
        world = s.report(dates=("2028-05-01",))["worlds"][0]
        self.assertEqual(world["outcomes"][1]["status"], "PREDECESSOR_NOT_EFFECTIVE")
        self.assertEqual(world["dated_stock"][0]["state_mass"][("cell", "BASE")], F("10.5"))
        self.assertEqual(world["dated_stock"][0]["state_mass"][("cell", "PACKAGE")], 0)
        self.assertEqual(world["dated_stock"][0]["state_mass"][("cell", "LATER")], 0)


if __name__ == "__main__":
    unittest.main()
