import datetime
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from .models import (
    UserProfile, UserRole, Election, ElectionCategory, ElectionStatus,
    Candidate, Ballot, VoterParticipation, AuditLog
)


class BallotBridgeVotingSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test voter
        self.user = User.objects.create_user(
            username='test_voter',
            password='TestPassword123!',
            email='voter@test.com',
            first_name='Test',
            last_name='Voter'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            role=UserRole.VOTER,
            voter_id='BB-TEST-001',
            demo_id_number='DEMO-1234',
            organization='Test Organization',
            department='Test Department',
            is_verified=True
        )

        now = timezone.now()

        # Create active election
        self.active_election = Election.objects.create(
            title='Active Test Election',
            slug='active-test-election',
            description='Test description',
            category=ElectionCategory.NATIONAL_YOUTH,
            status=ElectionStatus.ACTIVE,
            start_time=now - datetime.timedelta(hours=2),
            end_time=now + datetime.timedelta(hours=2),
            eligibility_criteria='ALL'
        )

        # Candidates for active election
        self.cand_a = Candidate.objects.create(
            election=self.active_election,
            name='Candidate Alpha',
            ballot_number=1,
            party_or_slate='Alliance A',
            short_bio='Bio A',
            qualifications='Qual A',
            manifesto='Manifesto A',
            key_proposals='Proposal 1\nProposal 2'
        )

        self.cand_b = Candidate.objects.create(
            election=self.active_election,
            name='Candidate Beta',
            ballot_number=2,
            party_or_slate='Alliance B',
            short_bio='Bio B',
            qualifications='Qual B',
            manifesto='Manifesto B',
            key_proposals='Proposal 3\nProposal 4'
        )

        # Create scheduled (future) election
        self.scheduled_election = Election.objects.create(
            title='Scheduled Test Election',
            slug='scheduled-test-election',
            description='Scheduled description',
            category=ElectionCategory.CIVIC,
            status=ElectionStatus.SCHEDULED,
            start_time=now + datetime.timedelta(days=1),
            end_time=now + datetime.timedelta(days=3),
            eligibility_criteria='ALL'
        )
        self.cand_scheduled = Candidate.objects.create(
            election=self.scheduled_election,
            name='Candidate Gamma',
            ballot_number=1,
            short_bio='Bio G',
            qualifications='Qual G',
            manifesto='Manifesto G',
            key_proposals='Proposal 5'
        )

    def test_authenticated_voter_can_cast_ballot(self):
        """Test standard simulated voting workflow: login -> select candidate -> submit"""
        self.client.login(username='test_voter', password='TestPassword123!')
        
        # Submit vote
        response = self.client.post(
            reverse('vote_submit', kwargs={'slug': self.active_election.slug}),
            {'candidate_id': self.cand_a.id},
            follow=True
        )

        # 1. Ballot was created
        self.assertEqual(Ballot.objects.filter(election=self.active_election).count(), 1)
        ballot = Ballot.objects.filter(election=self.active_election).first()
        self.assertEqual(ballot.candidate, self.cand_a)

        # 2. Participation record was created without storing candidate
        participation = VoterParticipation.objects.filter(user=self.user, election=self.active_election).first()
        self.assertIsNotNone(participation)
        self.assertTrue(participation.receipt_token.startswith('BB-REC-'))

        # 3. Secret Ballot Verification: Ballot model does not contain user foreign key
        self.assertFalse(hasattr(ballot, 'user'))

        # 4. Success message shown
        self.assertContains(response, "Your vote has been securely and anonymously recorded")

    def test_one_vote_per_voter_enforcement(self):
        """Test database and view constraint: a voter CANNOT cast more than one ballot in the same election"""
        self.client.login(username='test_voter', password='TestPassword123!')

        # First vote
        self.client.post(
            reverse('vote_submit', kwargs={'slug': self.active_election.slug}),
            {'candidate_id': self.cand_a.id}
        )
        self.assertEqual(Ballot.objects.filter(election=self.active_election).count(), 1)

        # Attempt second vote in the same election
        response2 = self.client.post(
            reverse('vote_submit', kwargs={'slug': self.active_election.slug}),
            {'candidate_id': self.cand_b.id},
            follow=True
        )

        # Ballot count must STILL be 1 (second vote rejected!)
        self.assertEqual(Ballot.objects.filter(election=self.active_election).count(), 1)
        self.assertContains(response2, "You have already cast a vote in this election")

    def test_cannot_vote_in_scheduled_election(self):
        """Server-side validation must reject votes if election is not ACTIVE"""
        self.client.login(username='test_voter', password='TestPassword123!')

        response = self.client.post(
            reverse('vote_submit', kwargs={'slug': self.scheduled_election.slug}),
            {'candidate_id': self.cand_scheduled.id},
            follow=True
        )

        self.assertEqual(Ballot.objects.filter(election=self.scheduled_election).count(), 0)
        self.assertContains(response, "Election is not currently accepting ballots")

    def test_results_hidden_before_publication(self):
        """Results endpoint must return locked view when status is not RESULTS_PUBLISHED"""
        response = self.client.get(reverse('results', kwargs={'slug': self.active_election.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Election Results are Sealed")
        self.assertNotContains(response, "Certified Official Outcome")

    def test_results_displayed_when_published(self):
        """Results endpoint displays data and candidate tally when RESULTS_PUBLISHED"""
        # Close and publish election
        self.active_election.status = ElectionStatus.RESULTS_PUBLISHED
        self.active_election.save()

        # Add sample ballot
        b_hash = "test_hash_123"
        Ballot.objects.create(election=self.active_election, candidate=self.cand_a, ballot_hash=b_hash)

        response = self.client.get(reverse('results', kwargs={'slug': self.active_election.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certified Official Outcome")
        self.assertContains(response, "Candidate Alpha")
