import hashlib
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class UserRole(models.TextChoices):
    VOTER = 'VOTER', 'Voter'
    ADMIN = 'ADMIN', 'Election Administrator'
    CANDIDATE = 'CANDIDATE', 'Candidate Representative'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VOTER)
    voter_id = models.CharField(max_length=32, unique=True, db_index=True)
    demo_id_number = models.CharField(max_length=64, blank=True, default='', help_text='Simulated national or student ID')
    organization = models.CharField(max_length=120, blank=True, default='National Voter Registry')
    department = models.CharField(max_length=120, blank=True, default='General Division')
    is_verified = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=30, blank=True, default='')
    avatar_color = models.CharField(max_length=20, default='#0284c7')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.voter_id}) [{self.role}]"

    @property
    def is_admin_role(self):
        return self.role == UserRole.ADMIN or self.user.is_superuser or self.user.is_staff


class ElectionCategory(models.TextChoices):
    STUDENT_GOV = 'STUDENT_GOV', 'Student Government'
    CIVIC = 'CIVIC', 'Civic & Municipal'
    CORPORATE = 'CORPORATE', 'Corporate & Board'
    NATIONAL_YOUTH = 'NATIONAL_YOUTH', 'National Youth Council'
    ACADEMIC = 'ACADEMIC', 'Academic Council'


class ElectionStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    ACTIVE = 'ACTIVE', 'Active (Voting Open)'
    CLOSED = 'CLOSED', 'Closed (Voting Ended)'
    RESULTS_PUBLISHED = 'RESULTS_PUBLISHED', 'Results Published'


class Election(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    tagline = models.CharField(max_length=255, blank=True, default='Empowering community decision making')
    description = models.TextField(help_text='Detailed information regarding election purpose and scope')
    category = models.CharField(max_length=30, choices=ElectionCategory.choices, default=ElectionCategory.NATIONAL_YOUTH)
    status = models.CharField(max_length=25, choices=ElectionStatus.choices, default=ElectionStatus.SCHEDULED)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    eligibility_criteria = models.CharField(
        max_length=50,
        choices=[
            ('ALL', 'All Registered Voters'),
            ('STUDENTS', 'Registered Students Only'),
            ('FACULTY', 'Academic Faculty Only'),
            ('COMMUNITY', 'Community Members'),
        ],
        default='ALL'
    )
    banner_color = models.CharField(max_length=25, default='#1e3a8a')
    banner_icon = models.CharField(max_length=50, default='vote')
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_elections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'election'
            unique_slug = base_slug
            counter = 1
            while Election.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"

    def is_voting_open(self):
        """Strict server-side validation of active voting window"""
        now = timezone.now()
        return self.status == ElectionStatus.ACTIVE and self.start_time <= now <= self.end_time

    def is_closed_or_published(self):
        return self.status in [ElectionStatus.CLOSED, ElectionStatus.RESULTS_PUBLISHED]

    def has_user_voted(self, user):
        if not user or not user.is_authenticated:
            return False
        return VoterParticipation.objects.filter(election=self, user=user).exists()

    def user_voting_receipt(self, user):
        if not user or not user.is_authenticated:
            return None
        participation = VoterParticipation.objects.filter(election=self, user=user).first()
        return participation.receipt_token if participation else None

    def is_user_eligible(self, user):
        if not user or not user.is_authenticated:
            return False, "You must be logged in to vote."
        if not hasattr(user, 'profile') or not user.profile.is_verified:
            return False, "Your voter profile is pending verification."
        
        # Check category specific criteria
        criteria = self.eligibility_criteria
        if criteria == 'ALL':
            return True, "Eligible to participate"
        elif criteria == 'STUDENTS':
            if 'Student' in user.profile.department or 'College' in user.profile.organization:
                return True, "Eligible student voter"
            return False, "This election is restricted to verified student voters."
        elif criteria == 'FACULTY':
            if 'Faculty' in user.profile.department or 'Academic' in user.profile.department:
                return True, "Eligible faculty voter"
            return False, "This election is restricted to faculty members."
        return True, "Eligible voter"

    def total_votes_cast(self):
        return self.ballots.count()

    def eligible_voters_count(self):
        # Simulated count based on registered profiles matching criteria
        total_profiles = UserProfile.objects.filter(role=UserRole.VOTER, is_verified=True).count()
        return max(total_profiles, self.total_votes_cast())

    def turnout_percentage(self):
        eligible = self.eligible_voters_count()
        if eligible == 0:
            return 0.0
        return round((self.total_votes_cast() / eligible) * 100, 1)

    def get_results_data(self):
        """Returns structured results with percentages and candidate details"""
        if self.status != ElectionStatus.RESULTS_PUBLISHED:
            return None
        
        total_votes = self.total_votes_cast()
        results = []
        highest_votes = -1

        candidates = self.candidates.all()
        for cand in candidates:
            cand_votes = cand.ballots.count()
            pct = round((cand_votes / total_votes * 100), 2) if total_votes > 0 else 0.0
            if cand_votes > highest_votes:
                highest_votes = cand_votes
            results.append({
                'candidate': cand,
                'votes': cand_votes,
                'percentage': pct,
                'is_winner': False,
            })

        # Determine winner or tie
        if total_votes > 0 and highest_votes > 0:
            top_candidates = [r for r in results if r['votes'] == highest_votes]
            is_tie = len(top_candidates) > 1
            for r in results:
                if r['votes'] == highest_votes:
                    r['is_winner'] = not is_tie
                    r['is_tie'] = is_tie
                else:
                    r['is_tie'] = False
        else:
            is_tie = False
            for r in results:
                r['is_tie'] = False

        # Sort descending by votes
        results.sort(key=lambda x: x['votes'], reverse=True)

        return {
            'results': results,
            'total_votes': total_votes,
            'turnout_percentage': self.turnout_percentage(),
            'eligible_voters': self.eligible_voters_count(),
            'is_tie': is_tie if total_votes > 0 else False,
            'top_count': highest_votes,
        }


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=150)
    ballot_number = models.PositiveIntegerField(default=1)
    party_or_slate = models.CharField(max_length=150, blank=True, default='Independent')
    role_title = models.CharField(max_length=150, blank=True, default='Candidate for Office')
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    avatar_color = models.CharField(max_length=20, default='#0284c7')
    avatar_initials = models.CharField(max_length=4, blank=True, default='')
    short_bio = models.TextField(help_text='Concise summary of experience and values')
    qualifications = models.TextField(help_text='Educational, professional, and leadership credentials')
    manifesto = models.TextField(help_text='Official campaign manifesto statement')
    key_proposals = models.TextField(help_text='Key proposal points, separated by newlines')
    email = models.EmailField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ballot_number', 'name']

    def save(self, *args, **kwargs):
        if not self.avatar_initials and self.name:
            names = self.name.split()
            if len(names) >= 2:
                self.avatar_initials = f"{names[0][0]}{names[1][0]}".upper()
            else:
                self.avatar_initials = self.name[:2].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.ballot_number} {self.name} - {self.election.title}"

    def get_proposals_list(self):
        return [p.strip() for p in self.key_proposals.splitlines() if p.strip()]

    def get_qualifications_list(self):
        return [q.strip() for q in self.qualifications.splitlines() if q.strip()]

    def current_votes_count(self):
        return self.ballots.count()


class Ballot(models.Model):
    """
    CRITICAL ANONYMOUS BALLOT RECORD:
    To preserve genuine democratic secret ballot principles, this record stores
    the vote choice linked ONLY to the election and candidate, with ZERO reference
    to the voter identity (User).
    """
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='ballots')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ballots')
    ballot_hash = models.CharField(max_length=64, unique=True, db_index=True)
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-cast_at']

    def __str__(self):
        return f"EncryptedBallot[{self.ballot_hash[:12]}...] in {self.election.title}"


class VoterParticipation(models.Model):
    """
    PARTICIPATION LEDGER:
    Tracks that an authenticated voter has cast their single permitted ballot in
    a specific election. Enforces strict one-person-one-vote database constraint
    WITHOUT recording which candidate was selected.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voting_records')
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='participations')
    voted_at = models.DateTimeField(auto_now_add=True)
    receipt_token = models.CharField(max_length=64, unique=True, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        unique_together = ('user', 'election')
        ordering = ['-voted_at']

    def __str__(self):
        return f"{self.user.username} voted in {self.election.title} [Receipt: {self.receipt_token[:10]}...]"


class AuditLog(models.Model):
    class Severity(models.TextChoices):
        INFO = 'INFO', 'Information'
        WARNING = 'WARNING', 'Warning'
        SECURITY = 'SECURITY', 'Security Alert'

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    details = models.TextField()
    ip_address = models.CharField(max_length=50, blank=True, default='')
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.severity}] {self.timestamp:%Y-%m-%d %H:%M} - {user_str}: {self.action}"


class Announcement(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title
