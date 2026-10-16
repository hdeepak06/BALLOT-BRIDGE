import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from voting.models import (
    UserProfile, UserRole, Election, ElectionCategory, ElectionStatus,
    Candidate, Ballot, VoterParticipation, AuditLog, Announcement
)
from voting.utils import generate_voter_id, generate_ballot_hash, generate_receipt_token


class Command(BaseCommand):
    help = 'Seeds realistic demonstration elections, candidates, audit logs, and demo users.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Initializing BallotBridge seed data...")

        # 1. CREATE DEMO ACCOUNTS
        # Administrator
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ballotbridge.demo',
                'first_name': 'Chief',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin12345')
        admin_user.save()

        UserProfile.objects.update_or_create(
            user=admin_user,
            defaults={
                'role': UserRole.ADMIN,
                'voter_id': 'BB-ADM-001',
                'demo_id_number': 'ELEC-COMM-001',
                'organization': 'Central Election Commission',
                'department': 'Electoral Governance Board',
                'is_verified': True,
                'avatar_color': '#0f172a'
            }
        )

        # Voter 1: Alex Morgan (Ready to vote)
        voter_alex, _ = User.objects.get_or_create(
            username='voter_alex',
            defaults={
                'email': 'alex.morgan@demo.edu',
                'first_name': 'Alex',
                'last_name': 'Morgan',
            }
        )
        voter_alex.set_password('voter12345')
        voter_alex.save()

        UserProfile.objects.update_or_create(
            user=voter_alex,
            defaults={
                'role': UserRole.VOTER,
                'voter_id': 'BB-2026-78421',
                'demo_id_number': 'STU-99201',
                'organization': 'Metropolitan University',
                'department': 'College of Engineering & Sciences',
                'is_verified': True,
                'avatar_color': '#0d9488'
            }
        )

        # Voter 2: Priya Sharma (Pre-voted in one election)
        voter_priya, _ = User.objects.get_or_create(
            username='voter_priya',
            defaults={
                'email': 'priya.sharma@demo.org',
                'first_name': 'Priya',
                'last_name': 'Sharma',
            }
        )
        voter_priya.set_password('voter12345')
        voter_priya.save()

        UserProfile.objects.update_or_create(
            user=voter_priya,
            defaults={
                'role': UserRole.VOTER,
                'voter_id': 'BB-2026-89104',
                'demo_id_number': 'CIT-55219',
                'organization': 'Metropolitan Civic Alliance',
                'department': 'Public Member',
                'is_verified': True,
                'avatar_color': '#0284c7'
            }
        )

        # Voter 3: David Chen
        voter_david, _ = User.objects.get_or_create(
            username='voter_david',
            defaults={
                'email': 'david.chen@demo.org',
                'first_name': 'David',
                'last_name': 'Chen',
            }
        )
        voter_david.set_password('voter12345')
        voter_david.save()

        UserProfile.objects.update_or_create(
            user=voter_david,
            defaults={
                'role': UserRole.VOTER,
                'voter_id': 'BB-2026-64112',
                'demo_id_number': 'STU-88310',
                'organization': 'Metropolitan University',
                'department': 'School of Business',
                'is_verified': True,
                'avatar_color': '#4f46e5'
            }
        )

        # 2. CREATE ELECTIONS
        now = timezone.now()

        # ELECTION 1: ACTIVE NOW
        el_youth, _ = Election.objects.get_or_create(
            slug='2026-national-youth-tech-climate-council',
            defaults={
                'title': '2026 National Youth Tech & Climate Council',
                'tagline': 'Shaping sustainable technology policy and youth climate governance',
                'description': 'Electing the national executive committee responsible for youth-driven environmental oversight, open data access, and civic tech innovation.',
                'category': ElectionCategory.NATIONAL_YOUTH,
                'status': ElectionStatus.ACTIVE,
                'start_time': now - datetime.timedelta(days=2),
                'end_time': now + datetime.timedelta(days=3),
                'eligibility_criteria': 'ALL',
                'banner_color': '#0d9488',
                'is_featured': True,
                'created_by': admin_user,
            }
        )

        # Candidates for Election 1
        cand_maya, _ = Candidate.objects.get_or_create(
            election=el_youth,
            ballot_number=1,
            defaults={
                'name': 'Maya Lin',
                'party_or_slate': 'Green Future Coalition',
                'role_title': 'Council Chair Nominee',
                'avatar_color': '#059669',
                'short_bio': 'Environmental scientist and youth climate activist leading local regenerative energy advocacy and open environmental metrics.',
                'qualifications': 'B.Sc. Environmental Science, Former President of Youth Action for Clean Air, 4 years community organizer.',
                'manifesto': 'Our platform centers on three pillars: transparent carbon footprint auditing across municipal facilities, mandatory youth representation on climate advisory boards, and community-owned renewable energy microgrids.',
                'key_proposals': 'Mandate real-time air quality sensor networks\nEstablish youth climate innovation grants\nPromote solar canopy installations in public campuses',
                'email': 'maya.lin@greenfuture.demo'
            }
        )

        cand_jordan, _ = Candidate.objects.get_or_create(
            election=el_youth,
            ballot_number=2,
            defaults={
                'name': 'Jordan Taylor',
                'party_or_slate': 'Civic Tech & Open Governance Alliance',
                'role_title': 'Council Chair Nominee',
                'avatar_color': '#0284c7',
                'short_bio': 'Open-source software advocate and public digital infrastructure researcher focused on privacy-preserving democratic tools.',
                'qualifications': 'M.S. Computer Science, Maintainer of Open Democracy Toolkit, Lead Developer on Public Budgeting Portal.',
                'manifesto': 'Technology should empower people, not surveil them. I propose deploying open-source data pipelines for all municipal expenditures, zero-knowledge privacy guarantees in civic portals, and free broadband in underserved neighborhoods.',
                'key_proposals': 'Launch public open budget visualizers\nDecentralize community ballot infrastructure\nProvide subsidized internet access to student housing',
                'email': 'jordan.taylor@civictech.demo'
            }
        )

        cand_liam, _ = Candidate.objects.get_or_create(
            election=el_youth,
            ballot_number=3,
            defaults={
                'name': 'Liam Sterling',
                'party_or_slate': 'Independent Youth Voice',
                'role_title': 'Council Chair Nominee',
                'avatar_color': '#d97706',
                'short_bio': 'Social entrepreneur and community organizer promoting youth apprenticeship, financial literacy, and mental health access.',
                'qualifications': 'Co-founder of Metro Youth Mentorship, 3 years Regional Youth Representative, Certified Mediator.',
                'manifesto': 'Real change starts with pragmatic opportunities. My agenda prioritizes expanding paid technical internships, improving youth mental health counseling availability, and ensuring all community forums are accessible to working youth.',
                'key_proposals': 'Double paid technical apprentice placements\n24/7 peer-supported mental wellbeing hotline\nDecentralized local youth councils in every district',
                'email': 'liam.sterling@independent.demo'
            }
        )

        # Pre-seed Priya's vote in Election 1 to demonstrate "Already Voted" state
        if not VoterParticipation.objects.filter(user=voter_priya, election=el_youth).exists():
            b_hash = generate_ballot_hash(el_youth.id, cand_maya.id)
            r_token = generate_receipt_token(voter_priya.id, el_youth.id)
            Ballot.objects.create(election=el_youth, candidate=cand_maya, ballot_hash=b_hash)
            VoterParticipation.objects.create(user=voter_priya, election=el_youth, receipt_token=r_token, ip_hash=b_hash[:16])

        # Pre-seed simulated anonymous ballots for Turnout in Election 1
        if el_youth.ballots.count() < 12:
            sim_votes = [
                (cand_maya, 6),
                (cand_jordan, 5),
                (cand_liam, 3),
            ]
            for cand, count in sim_votes:
                for _ in range(count):
                    b_hash = generate_ballot_hash(el_youth.id, cand.id)
                    Ballot.objects.create(election=el_youth, candidate=cand, ballot_hash=b_hash)

        # ELECTION 2: ACTIVE (Student Senate)
        el_senate, _ = Election.objects.get_or_create(
            slug='metropolitan-university-student-senate-president',
            defaults={
                'title': 'Metropolitan University Student Senate President',
                'tagline': 'Electing the undergraduate student body president and senate leadership',
                'description': 'The Student Senate President represents 18,000 students on the University Board of Trustees and oversees allocation of the student activity endowment.',
                'category': ElectionCategory.STUDENT_GOV,
                'status': ElectionStatus.ACTIVE,
                'start_time': now - datetime.timedelta(days=1),
                'end_time': now + datetime.timedelta(days=2),
                'eligibility_criteria': 'ALL',
                'banner_color': '#4f46e5',
                'is_featured': True,
                'created_by': admin_user,
            }
        )

        Candidate.objects.get_or_create(
            election=el_senate,
            ballot_number=1,
            defaults={
                'name': 'Sophia Al-Mansoor',
                'party_or_slate': 'Students for Accessible Education',
                'role_title': 'Presidential Candidate',
                'avatar_color': '#0284c7',
                'short_bio': 'Senior Political Science student and former Senator for Liberal Arts advocating for textbook affordability and student housing rights.',
                'qualifications': 'Junior Senator 2024-2025, Chair of Tuition Transparency Committee, Dean\'s Honor List.',
                'manifesto': 'Higher education must be accessible to all students regardless of economic background. We will expand open educational textbook resources and cap campus dining price increases.',
                'key_proposals': 'Freeze mandatory lab and technology fees\nExpand 24-hour campus study commons\nUniversal digital transit pass for all enrolled students',
                'email': 'sophia.almansoor@metro.edu'
            }
        )

        Candidate.objects.get_or_create(
            election=el_senate,
            ballot_number=2,
            defaults={
                'name': 'Lucas Bennett',
                'party_or_slate': 'Campus Innovation & Sustainability',
                'role_title': 'Presidential Candidate',
                'avatar_color': '#0d9488',
                'short_bio': 'Mechanical Engineering junior and president of the Solar Racing Team committed to a net-zero campus and student venture incubators.',
                'qualifications': 'President of Clean Tech Club, Student Representative on Campus Planning Committee.',
                'manifesto': 'We believe in practical, high-impact improvements: zero-waste dining facilities, expanded campus cycling lanes, and competitive seed funding for student startups.',
                'key_proposals': 'Install solar charging benches across all campus quads\nCreate $50,000 student venture innovation micro-fund\nUpgrade campus bike sharing program',
                'email': 'lucas.bennett@metro.edu'
            }
        )

        Candidate.objects.get_or_create(
            election=el_senate,
            ballot_number=3,
            defaults={
                'name': 'Aaliyah Washington',
                'party_or_slate': 'Wellbeing & Inclusion Coalition',
                'role_title': 'Presidential Candidate',
                'avatar_color': '#ec4899',
                'short_bio': 'Psychology senior and peer counselor working to expand mental health access and equitable campus disability accommodations.',
                'qualifications': 'Peer Wellness Coordinator, Member of Diversity & Inclusion Advisory Board, 300+ volunteer hours.',
                'manifesto': 'Student well-being directly impacts academic success. Our coalition will reduce wait times for counseling and ensure neurodivergent students receive prompt accommodations.',
                'key_proposals': 'Hire additional licensed mental health counselors\nQuiet study and sensory decompressed spaces in libraries\nEmergency student housing and food security pantry funding',
                'email': 'aaliyah.washington@metro.edu'
            }
        )

        # Pre-seed anonymous ballots for Election 2
        if el_senate.ballots.count() < 15:
            cand_sophia = Candidate.objects.filter(election=el_senate, ballot_number=1).first()
            cand_lucas = Candidate.objects.filter(election=el_senate, ballot_number=2).first()
            cand_aaliyah = Candidate.objects.filter(election=el_senate, ballot_number=3).first()
            for cand, count in [(cand_sophia, 8), (cand_lucas, 7), (cand_aaliyah, 5)]:
                for _ in range(count):
                    b_hash = generate_ballot_hash(el_senate.id, cand.id)
                    Ballot.objects.create(election=el_senate, candidate=cand, ballot_hash=b_hash)

        # ELECTION 3: RESULTS PUBLISHED (Closed & Certified)
        el_published, _ = Election.objects.get_or_create(
            slug='2025-national-innovation-leadership-council',
            defaults={
                'title': '2025 National Innovation Leadership Council',
                'tagline': 'Certified national election determining research priorities and ethics oversight',
                'description': 'Concluded national election selecting the Board of Directors for Science and Innovation Research.',
                'category': ElectionCategory.CIVIC,
                'status': ElectionStatus.RESULTS_PUBLISHED,
                'start_time': now - datetime.timedelta(days=15),
                'end_time': now - datetime.timedelta(days=2),
                'eligibility_criteria': 'ALL',
                'banner_color': '#1e3a8a',
                'is_featured': False,
                'created_by': admin_user,
            }
        )

        cand_aris, _ = Candidate.objects.get_or_create(
            election=el_published,
            ballot_number=1,
            defaults={
                'name': 'Dr. Aris Thorne',
                'party_or_slate': 'Scientific Integrity & Public Benefit',
                'role_title': 'Council Director Nominee',
                'avatar_color': '#0d9488',
                'short_bio': 'Senior bioethicist and research fellow at the National Science Foundation focusing on open access publishing and AI safety standards.',
                'qualifications': 'Ph.D. Bioethics, 15 peer-reviewed publications, Former Advisor to the National Science Board.',
                'manifesto': 'Scientific breakthroughs must serve the common good. We advocate for free public access to all taxpayer-funded research papers and strict safety auditing for automated decision systems.',
                'key_proposals': 'Mandate Open Access for publicly funded scientific publications\nEstablish National AI Safety & Ethics Review Board\nExpand early-career research grant allocations by 35%',
                'email': 'aris.thorne@science.demo'
            }
        )

        cand_nadia, _ = Candidate.objects.get_or_create(
            election=el_published,
            ballot_number=2,
            defaults={
                'name': 'Nadia Patel',
                'party_or_slate': 'Collaborative Innovation Alliance',
                'role_title': 'Council Director Nominee',
                'avatar_color': '#4f46e5',
                'short_bio': 'Deep-tech founder and clean energy venture fellow bridging academic laboratories with industrial manufacturing pipelines.',
                'qualifications': 'M.Eng. Nanotechnology, Founder of 2 clean-tech spinouts, MIT Tech Review 35 Under 35 Honoree.',
                'manifesto': 'Accelerating research commercialization to solve climate challenges and medical frontiers. We must bridge academic discoveries with scalable manufacturing.',
                'key_proposals': 'Create regional technology commercialization accelerators\nTax credits for industrial research collaboration\nStreamlined patent licensing for academic breakthroughs',
                'email': 'nadia.patel@innovation.demo'
            }
        )

        cand_samuel, _ = Candidate.objects.get_or_create(
            election=el_published,
            ballot_number=3,
            defaults={
                'name': 'Samuel O\'Connor',
                'party_or_slate': 'Regional Equity in Tech Coalition',
                'role_title': 'Council Director Nominee',
                'avatar_color': '#f59e0b',
                'short_bio': 'Regional development director focused on distributing research investments beyond traditional coastal tech corridors.',
                'qualifications': 'Former Director of Regional STEM Outreach, 12 years municipal development director.',
                'manifesto': 'Innovation shouldn\'t just happen in two metropolitan hubs. We need decentralized research institutes across the entire country.',
                'key_proposals': 'Decentralize federal research grant allocations\nInvest in rural and suburban university laboratory upgrades\nNationwide high-speed computing network access',
                'email': 'samuel.oconnor@equity.demo'
            }
        )

        # Seed realistic ballot tallies for Election 3 (Published Results)
        if el_published.ballots.count() < 40:
            votes_distribution = [
                (cand_aris, 26),    # Winner
                (cand_nadia, 15),
                (cand_samuel, 9),
            ]
            for cand, count in votes_distribution:
                for _ in range(count):
                    b_hash = generate_ballot_hash(el_published.id, cand.id)
                    Ballot.objects.create(election=el_published, candidate=cand, ballot_hash=b_hash)

        # ELECTION 4: SCHEDULED (Upcoming)
        el_scheduled, _ = Election.objects.get_or_create(
            slug='global-open-source-governance-board-2026',
            defaults={
                'title': 'Global Open-Source Governance Board 2026',
                'tagline': 'Electing the community steering committee for open digital public infrastructure',
                'description': 'Upcoming election for the 2026 steering committee governing open protocol standards, developer security grants, and international software freedom.',
                'category': ElectionCategory.CORPORATE,
                'status': ElectionStatus.SCHEDULED,
                'start_time': now + datetime.timedelta(days=4),
                'end_time': now + datetime.timedelta(days=11),
                'eligibility_criteria': 'ALL',
                'banner_color': '#0284c7',
                'is_featured': False,
                'created_by': admin_user,
            }
        )

        Candidate.objects.get_or_create(
            election=el_scheduled,
            ballot_number=1,
            defaults={
                'name': 'Helena Vasquez',
                'party_or_slate': 'Developer Autonomy Slate',
                'role_title': 'Board Member Candidate',
                'avatar_color': '#14b8a6',
                'short_bio': 'Kernel maintainer and open-source foundation trustee advocating for independent developer funding and reproducible builds.',
                'qualifications': '12 years open-source maintainer, Security Committee Chair at Open Source Initiative.',
                'manifesto': 'Open source infrastructure underpins the global digital economy. We must establish sustainable recurring grant pools for unpaid maintainers of critical libraries.',
                'key_proposals': 'Dedicated security audit grants for high-traffic packages\nLegal defense fund for open source developers\nGlobal reproducible build verification standards',
                'email': 'helena.vasquez@opensource.demo'
            }
        )

        Candidate.objects.get_or_create(
            election=el_scheduled,
            ballot_number=2,
            defaults={
                'name': 'Marcus Vance',
                'party_or_slate': 'Enterprise & Community Federation',
                'role_title': 'Board Member Candidate',
                'avatar_color': '#6366f1',
                'short_bio': 'Engineering VP and corporate open source sponsor advocating for healthy multi-stakeholder governance and compliance automation.',
                'qualifications': 'VP Engineering, author of Software Bill of Materials standards, 18 years software architecture.',
                'manifesto': 'Balancing enterprise sustainability with community autonomy. We foster corporate sponsorships that preserve project neutrality and open licensing.',
                'key_proposals': 'Automated SBOM compliance pipelines\nCorporate sponsorship tax framework optimization\nCommunity mentorship and diversity onboarding fellowships',
                'email': 'marcus.vance@federation.demo'
            }
        )

        # 3. CREATE ANNOUNCEMENTS
        Announcement.objects.get_or_create(
            title="Notice: 2026 National Youth Tech & Climate Council Voting Is Live",
            defaults={
                'election': el_youth,
                'message': "Confidential ballots are currently being accepted. Review all candidate manifestos and verify your receipt token upon voting.",
                'is_pinned': True,
            }
        )

        Announcement.objects.get_or_create(
            title="Results Certified: 2025 National Innovation Leadership Council",
            defaults={
                'election': el_published,
                'message': "Official ballot tallying is complete and certified. Detailed Chart.js analytics and candidate breakdowns are available on the results page.",
                'is_pinned': True,
            }
        )

        # 4. CREATE AUDIT LOGS
        AuditLog.objects.get_or_create(
            action='ELECTION_SYSTEM_INITIALIZED',
            defaults={
                'user': admin_user,
                'details': 'BallotBridge simulation environment initialized with cryptographic double-blind separation and server-side validation.',
                'severity': AuditLog.Severity.INFO,
                'ip_address': '127.0.0.1'
            }
        )

        AuditLog.objects.get_or_create(
            action='RESULTS_PUBLISHED',
            defaults={
                'user': admin_user,
                'details': f"Certified results officially released for '{el_published.title}'. Total certified votes: {el_published.total_votes_cast()}",
                'severity': AuditLog.Severity.SECURITY,
                'ip_address': '127.0.0.1'
            }
        )

        AuditLog.objects.get_or_create(
            action='VOTING_WINDOW_OPENED',
            defaults={
                'user': admin_user,
                'details': f"Voting window transitioned to ACTIVE for '{el_youth.title}'.",
                'severity': AuditLog.Severity.INFO,
                'ip_address': '127.0.0.1'
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded BallotBridge demonstration database!"))
        self.stdout.write(self.style.SUCCESS("Demo accounts available:"))
        self.stdout.write(self.style.SUCCESS("  - Administrator: admin / admin12345"))
        self.stdout.write(self.style.SUCCESS("  - Voter (Ready to vote): voter_alex / voter12345"))
        self.stdout.write(self.style.SUCCESS("  - Voter (Pre-voted): voter_priya / voter12345"))
        self.stdout.write(self.style.SUCCESS("  - Voter (New): voter_david / voter12345"))
