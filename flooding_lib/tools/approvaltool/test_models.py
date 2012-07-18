from django.test import TestCase

from flooding_lib.tools.approvaltool import models


class TestApprovalObjectType(TestCase):
    def setUp(self):
        """Code assumes there is always a type with this type in the
        database. Probably ought to make it a fixture."""
        self.aot = models.ApprovalObjectType.objects.create(
            name=u"test",
            type=models.ApprovalObjectType.TYPE_PROJECT)

    def test_default_approval_type(self):
        """Check that the method returns something with the right type"""
        t = models.ApprovalObjectType.default_approval_type()
        self.assertEquals(t.type, models.ApprovalObjectType.TYPE_PROJECT)

    def test_unicode(self):
        self.assertEquals(unicode(self.aot), u"test")


class TestApprovalObjectState(TestCase):
    """No functionality yet, so no tests either"""
    pass


class TestApprovalObject(TestCase):
    def test_setup(self):
        # Create a approval object type with one rule
        aot = models.ApprovalObjectType.objects.create(
            name='test_aot',
            type=models.ApprovalObjectType.TYPE_ROR)
        aot.approvalrule.add(models.ApprovalRule.objects.create(
                name="test_rule",
                description="test",
                position=0))

        # Call the setup method
        ao = models.ApprovalObject.setup(
            name='test',
            approvalobjecttype=aot)

        # Now find its rules
        rules = list(models.ApprovalRule.objects.filter(
                approvalobject=ao))
        self.assertEquals(len(rules), 1)
        self.assertEquals(rules[0].name, 'test_rule')

    def test_state(self):
        aot = models.ApprovalObjectType.objects.create(
            name='test_aot',
            type=models.ApprovalObjectType.TYPE_ROR)
        rule = models.ApprovalRule.objects.create(
            name="test_rule",
            description="test",
            position=0)
        aot.approvalrule.add(rule)
        ao = models.ApprovalObject.setup(
            name='test',
            approvalobjecttype=aot)

        # ao.state returns a state object
        state = ao.state(rule)
        state.successful = True
        state.save()

        # but if we delete all the state objects, it returns a new one
        models.ApprovalObjectState.objects.filter(
            approvalobject=ao,
            approvalrule=rule).delete()
        state = ao.state(rule)
        self.assertNotEquals(state.successful, True)

    def test_states(self):
        # Create a approval object type with two rules
        aot = models.ApprovalObjectType.objects.create(
            name='test_aot',
            type=models.ApprovalObjectType.TYPE_ROR)
        rule1 = models.ApprovalRule.objects.create(
            name="test_rule1",
            description="test",
            position=2)
        rule2 = models.ApprovalRule.objects.create(
            name="test_rule2",
            description="test",
            position=1)

        aot.approvalrule.add(rule1)
        aot.approvalrule.add(rule2)

        ao = models.ApprovalObject.setup(
            name='test',
            approvalobjecttype=aot)

        states = list(ao.states())

        # Order should be reversed because of the positions
        self.assertEquals(len(states), 2)
        self.assertEquals(states[0].approvalrule, rule2)
        self.assertEquals(states[1].approvalrule, rule1)

        # No success entered yet
        self.assertEquals(states[0].successful, None)
        self.assertEquals(states[1].successful, None)

    def test_approve(self):
        # Create a approval object type with one rule
        aot = models.ApprovalObjectType.objects.create(
            name='test_aot',
            type=models.ApprovalObjectType.TYPE_ROR)
        rule = models.ApprovalRule.objects.create(
            name="test_rule",
            description="test",
            position=0)
        aot.approvalrule.add(rule)

        # Call the setup method
        ao = models.ApprovalObject.setup(
            name='test',
            approvalobjecttype=aot)

        # Approve!
        ao.approve(rule, True, 'test', 'testremarks')

        state = ao.states()[0]

        self.assertEquals(state.successful, True)
        self.assertEquals(state.creatorlog, 'test')
        self.assertEquals(state.remarks, 'testremarks')

        # Also present in the log?
        latest = models.ApprovalObjectLog.objects.filter(
            approvalobject=ao, approvalrule=rule).latest()

        self.assertEquals(latest.successful, True)
        self.assertEquals(latest.creatorlog, 'test')
        self.assertEquals(latest.remarks, 'testremarks')

    def test_approved_disapproved(self):
        # Create a approval object type with two rules
        aot = models.ApprovalObjectType.objects.create(
            name='test_aot',
            type=models.ApprovalObjectType.TYPE_ROR)
        rule1 = models.ApprovalRule.objects.create(
            name="test_rule1",
            description="test")
        rule2 = models.ApprovalRule.objects.create(
            name="test_rule2",
            description="test")

        aot.approvalrule.add(rule1)
        aot.approvalrule.add(rule2)

        # Call the setup method
        ao = models.ApprovalObject.setup(
            name='test',
            approvalobjecttype=aot)

        # None filled in -- neither approved nor disapproved
        self.assertFalse(ao.approved)
        self.assertFalse(ao.disapproved)

        state1 = models.ApprovalObjectState.objects.get(
            approvalobject=ao,
            approvalrule=rule1)
        state2 = models.ApprovalObjectState.objects.get(
            approvalobject=ao,
            approvalrule=rule2)

        # Set one rule to False -- disapproved True, approved False
        state1.successful = False
        state1.save()
        self.assertFalse(ao.approved)
        self.assertTrue(ao.disapproved)

        # That rule to True -- disapproved False, approved still False
        state1.successful = True
        state1.save()
        self.assertFalse(ao.approved)
        self.assertFalse(ao.disapproved)

        # Both to True -- disapproved False, approved True
        state1.successful = True
        state1.save()
        state2.successful = True
        state2.save()
        self.assertTrue(ao.approved)
        self.assertFalse(ao.disapproved)
