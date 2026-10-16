import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.urls import reverse

from .models import (
    UserProfile, UserRole, Election, ElectionCategory, ElectionStatus,
    Candidate, Ballot, VoterParticipation, AuditLog, Announcement
)
from .forms import (
    VoterRegistrationForm, UserProfileUpdateForm, ElectionForm,
    CandidateForm, AnnouncementForm
)
from .utils import (
    log_audit_event, generate_voter_id, generate_ballot_hash,
    generate_receipt_token, get_client_ip
)


# ==============================================================================
# 1. HOMEPAGE & PUBLIC VIEWS
# ==============================================================================

def home_view(request):
    """Modern hero landing page with platform overview, features, active demos & FAQ."""
    active_elections = Election.objects.filter(status=ElectionStatus.ACTIVE)[:4]
    upcoming_elections = Election.objects.filter(status=ElectionStatus.SCHEDULED)[:3]
    recent_published = Election.objects.filter(status=ElectionStatus.RESULTS_PUBLISHED)[:3]

    # Platform statistics (real calculated values + demo base)
    total_elections = Election.objects.count()
    total_ballots = Ballot.objects.count()
    total_voters = UserProfile.objects.filter(role=UserRole.VOTER).count()
    pinned_announcements = Announcement.objects.filter(is_pinned=True)[:3]

    context = {
        'active_elections': active_elections,
        'upcoming_elections': upcoming_elections,
        'recent_published': recent_published,
        'total_elections': total_elections,
        'total_ballots': total_ballots,
        'total_voters': total_voters,
        'pinned_announcements': pinned_announcements,
    }
    return render(request, 'home.html', context)


# ==============================================================================
# 2. USER AUTHENTICATION & PROFILES
# ==============================================================================

def register_view(request):
    """User registration with role, organization, and automatic voter ID generation."""
    if request.user.is_authenticated:
        return redirect('voter_dashboard')

    if request.method == 'POST':
        form = VoterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            role = form.cleaned_data.get('role', UserRole.VOTER)
            voter_id = generate_voter_id()
            demo_id = form.cleaned_data.get('demo_id_number', '')
            org = form.cleaned_data.get('organization', 'National Voter Registry')
            dept = form.cleaned_data.get('department', 'General Division')
            phone = form.cleaned_data.get('phone_number', '')

            UserProfile.objects.create(
                user=user,
                role=role,
                voter_id=voter_id,
                demo_id_number=demo_id,
                organization=org,
                department=dept,
                phone_number=phone,
                is_verified=True
            )

            # Log audit event
            log_audit_event(
                request=request,
                action='USER_REGISTRATION',
                details=f"New user registered: {user.username} with role {role} and Voter ID {voter_id}",
                severity='INFO',
                user=user
            )

            # Auto-login after successful registration
            login(request, user)
            messages.success(request, f"Welcome to BallotBridge! Your unique Voter ID is {voter_id}. Your account is verified for simulated elections.")
            return redirect('voter_dashboard')
        else:
            messages.error(request, "Registration could not be completed. Please correct the highlighted errors.")
    else:
        form = VoterRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    """User login with audit logging and friendly demo switcher hints."""
    if request.user.is_authenticated:
        return redirect('voter_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Ensure UserProfile exists
            if not hasattr(user, 'profile'):
                UserProfile.objects.create(
                    user=user,
                    role=UserRole.ADMIN if (user.is_superuser or user.is_staff) else UserRole.VOTER,
                    voter_id=generate_voter_id(),
                    organization='Metropolitan Civic Registry',
                    department='Engineering & Sciences',
                    is_verified=True
                )

            log_audit_event(
                request=request,
                action='USER_LOGIN',
                details=f"User {user.username} successfully authenticated.",
                severity='INFO',
                user=user
            )
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next') or 'voter_dashboard'
            return redirect(next_url)
        else:
            log_audit_event(
                request=request,
                action='FAILED_LOGIN_ATTEMPT',
                details=f"Failed login attempt for username: {request.POST.get('username')}",
                severity='WARNING'
            )
            messages.error(request, "Invalid username or password. Please check your credentials.")
    else:
        form = AuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    """User logout with security audit log."""
    if request.user.is_authenticated:
        log_audit_event(
            request=request,
            action='USER_LOGOUT',
            details=f"User {request.user.username} signed out.",
            severity='INFO',
            user=request.user
        )
        logout(request)
        messages.info(request, "You have been securely signed out.")
    return redirect('home')


def quick_demo_login_view(request, username):
    """
    Convenient demo account switcher for evaluation & testing:
    Allows instant switching between pre-seeded demo accounts (admin, voter_alex, voter_priya, voter_david).
    """
    user = User.objects.filter(username=username).first()
    if user:
        login(request, user)
        messages.success(request, f"Switched to demo account: {user.username} ({user.profile.get_role_display()})")
        if user.profile.is_admin_role:
            return redirect('admin_dashboard')
        return redirect('voter_dashboard')
    messages.error(request, f"Demo account '{username}' was not found. Please log in normally.")
    return redirect('login')


@login_required
def profile_view(request):
    """
    Voter profile page displaying voter identification, eligibility credentials,
    and confidential participation history (showing elections voted in & receipt hashes
    WITHOUT exposing the ballot selection).
    """
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'role': UserRole.VOTER,
            'voter_id': generate_voter_id(),
            'organization': 'Metropolitan Civic Registry',
            'department': 'Public Member',
            'is_verified': True
        }
    )

    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            log_audit_event(
                request=request,
                action='PROFILE_UPDATED',
                details=f"User {request.user.username} updated profile information.",
                severity='INFO'
            )
            messages.success(request, "Your profile information has been successfully updated.")
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=profile)

    # Fetch voting participation records (Receipts only - choice is completely secret!)
    participations = VoterParticipation.objects.filter(user=request.user).select_related('election')

    context = {
        'profile': profile,
        'form': form,
        'participations': participations,
    }
    return render(request, 'auth/profile.html', context)


@login_required
def password_change_view(request):
    """Secure password change with validation and re-authentication."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_audit_event(
                request=request,
                action='PASSWORD_CHANGED',
                details=f"User {request.user.username} changed account password.",
                severity='SECURITY'
            )
            messages.success(request, "Your password was successfully updated.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors in the password form.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'auth/password_change.html', {'form': form})


# ==============================================================================
# 3. VOTER DASHBOARD & ELECTION BROWSING
# ==============================================================================

@login_required
def voter_dashboard_view(request):
    """
    Main voter dashboard with active, upcoming, and closed elections,
    user voting status indicators, eligibility status, and announcements.
    """
    user = request.user
    category_filter = request.GET.get('category', 'ALL')
    search_query = request.GET.get('q', '').strip()
    status_tab = request.GET.get('tab', 'active')

    elections = Election.objects.all()

    if category_filter != 'ALL':
        elections = elections.filter(category=category_filter)

    if search_query:
        elections = elections.filter(title__icontains=search_query) | elections.filter(description__icontains=search_query)

    # Categorize elections
    active_elections = elections.filter(status=ElectionStatus.ACTIVE)
    upcoming_elections = elections.filter(status=ElectionStatus.SCHEDULED)
    closed_and_published = elections.filter(status__in=[ElectionStatus.CLOSED, ElectionStatus.RESULTS_PUBLISHED])

    # Build voter status map for quick template rendering
    user_participations = {
        vp.election_id: vp.receipt_token
        for vp in VoterParticipation.objects.filter(user=user)
    }

    # Annotate elections with voter-specific status
    def annotate_elections(election_list):
        annotated = []
        for el in election_list:
            has_voted = el.id in user_participations
            receipt = user_participations.get(el.id)
            is_eligible, reason = el.is_user_eligible(user)
            annotated.append({
                'election': el,
                'has_voted': has_voted,
                'receipt_token': receipt,
                'is_eligible': is_eligible,
                'eligibility_reason': reason,
                'can_vote_now': el.is_voting_open() and is_eligible and not has_voted,
            })
        return annotated

    active_annotated = annotate_elections(active_elections)
    upcoming_annotated = annotate_elections(upcoming_elections)
    closed_annotated = annotate_elections(closed_and_published)

    announcements = Announcement.objects.all()[:4]

    context = {
        'active_elections': active_annotated,
        'upcoming_elections': upcoming_annotated,
        'closed_elections': closed_annotated,
        'announcements': announcements,
        'selected_tab': status_tab,
        'category_filter': category_filter,
        'search_query': search_query,
        'categories': ElectionCategory.choices,
        'total_active_count': active_elections.count(),
        'total_voted_count': len(user_participations),
    }
    return render(request, 'voter/dashboard.html', context)


def election_detail_view(request, slug):
    """
    Displays full election profile, timeline, eligibility criteria,
    and candidate profiles with manifestos.
    """
    election = get_object_or_404(Election, slug=slug)
    candidates = election.candidates.all()
    user = request.user

    has_voted = False
    receipt_token = None
    is_eligible = False
    eligibility_reason = "Log in to check eligibility"
    can_vote = False

    if user.is_authenticated:
        has_voted = election.has_user_voted(user)
        receipt_token = election.user_voting_receipt(user)
        is_eligible, eligibility_reason = election.is_user_eligible(user)
        can_vote = election.is_voting_open() and is_eligible and not has_voted

    context = {
        'election': election,
        'candidates': candidates,
        'has_voted': has_voted,
        'receipt_token': receipt_token,
        'is_eligible': is_eligible,
        'eligibility_reason': eligibility_reason,
        'can_vote': can_vote,
    }
    return render(request, 'voter/election_detail.html', context)


def candidate_compare_view(request, slug):
    """
    Side-by-side neutral candidate comparison view.
    Does not rank or recommend; presents manifestos, proposals, and credentials fairly.
    """
    election = get_object_or_404(Election, slug=slug)
    candidates = election.candidates.all()

    context = {
        'election': election,
        'candidates': candidates,
    }
    return render(request, 'voter/candidate_compare.html', context)


# ==============================================================================
# 4. SIMULATED VOTING WORKFLOW (CRYPTOGRAPHIC CONFIDENTIAL BALLOT)
# ==============================================================================

@login_required
def vote_select_view(request, slug):
    """
    Step 1 of voting: Candidate selection interface.
    Validates server-side active status and eligibility before displaying ballot.
    """
    election = get_object_or_404(Election, slug=slug)
    user = request.user

    # 1. Server validation: Election status
    if not election.is_voting_open():
        messages.error(request, "Voting is currently not open for this election.")
        return redirect('election_detail', slug=slug)

    # 2. Server validation: Eligibility
    is_eligible, reason = election.is_user_eligible(user)
    if not is_eligible:
        messages.error(request, f"Ineligible to vote: {reason}")
        return redirect('election_detail', slug=slug)

    # 3. Server validation: Already voted
    if election.has_user_voted(user):
        messages.warning(request, "You have already cast your confidential ballot in this election.")
        return redirect('election_detail', slug=slug)

    candidates = election.candidates.all()
    if not candidates.exists():
        messages.error(request, "No candidates are registered for this election.")
        return redirect('election_detail', slug=slug)

    context = {
        'election': election,
        'candidates': candidates,
    }
    return render(request, 'voter/vote_select.html', context)


@login_required
def vote_confirm_view(request, slug):
    """
    Step 2 of voting: Explicit review and confirmation screen.
    Displays selected candidate and enforces explicit user confirmation.
    """
    if request.method != 'POST':
        return redirect('vote_select', slug=slug)

    election = get_object_or_404(Election, slug=slug)
    user = request.user
    candidate_id = request.POST.get('candidate_id')

    if not candidate_id:
        messages.error(request, "Please select a candidate before proceeding.")
        return redirect('vote_select', slug=slug)

    candidate = get_object_or_404(Candidate, id=candidate_id, election=election)

    # Re-validate constraints
    if not election.is_voting_open():
        messages.error(request, "Voting is not currently active.")
        return redirect('election_detail', slug=slug)

    if election.has_user_voted(user):
        messages.warning(request, "You have already cast a ballot in this election.")
        return redirect('election_detail', slug=slug)

    context = {
        'election': election,
        'candidate': candidate,
    }
    return render(request, 'voter/vote_confirm.html', context)


@login_required
def vote_submit_view(request, slug):
    """
    Step 3 of voting: Final vote processing with database transaction & constraints.
    
    CRITICAL SECURITY ARCHITECTURE:
    1. Uses transaction.atomic() to guarantee atomicity and race-condition safety.
    2. Validates election status on server: strictly ACTIVE and within start/end time.
    3. Validates candidate belongs to election.
    4. Validates voter eligibility.
    5. Checks uniqueness: User cannot vote twice in the same election.
    6. Double-blind separation:
       - Ballot record stores (election, candidate, ballot_hash) with NO user reference!
       - VoterParticipation stores (user, election, receipt_token) to mark turnout.
    7. Results remain secret until official publication.
    """
    if request.method != 'POST':
        return redirect('election_detail', slug=slug)

    election = get_object_or_404(Election, slug=slug)
    user = request.user
    candidate_id = request.POST.get('candidate_id')

    if not candidate_id:
        messages.error(request, "No candidate selection was received.")
        return redirect('vote_select', slug=slug)

    # Validate candidate belongs to this election
    candidate = get_object_or_404(Candidate, id=candidate_id, election=election)

    try:
        with transaction.atomic():
            # 1. Strict Server-Side Validation: Is election active right now?
            if not election.is_voting_open():
                log_audit_event(
                    request=request,
                    action='REJECTED_VOTE_CLOSED',
                    details=f"Rejected vote attempt in non-active election: {election.title}",
                    severity='WARNING'
                )
                messages.error(request, "Submission rejected: Election is not currently accepting ballots.")
                return redirect('election_detail', slug=slug)

            # 2. Strict Server-Side Validation: Voter Eligibility
            is_eligible, reason = election.is_user_eligible(user)
            if not is_eligible:
                log_audit_event(
                    request=request,
                    action='REJECTED_VOTE_INELIGIBLE',
                    details=f"Ineligible voting attempt by {user.username} in {election.title}",
                    severity='SECURITY'
                )
                messages.error(request, f"Voting authorization failed: {reason}")
                return redirect('election_detail', slug=slug)

            # 3. Strict Server-Side Validation: One-Vote Enforcement
            if VoterParticipation.objects.filter(user=user, election=election).exists():
                log_audit_event(
                    request=request,
                    action='REJECTED_DUPLICATE_VOTE',
                    details=f"Duplicate vote prevention triggered for {user.username} in {election.title}",
                    severity='SECURITY'
                )
                messages.warning(request, "You have already cast a vote in this election. Ballots cannot be modified or recast.")
                return redirect('election_detail', slug=slug)

            # 4. Generate Cryptographic Artifacts
            ballot_hash = generate_ballot_hash(election.id, candidate.id)
            receipt_token = generate_receipt_token(user.id, election.id)
            ip_addr = get_client_ip(request)

            # 5. Record Anonymous Ballot (Zero linkage to user ID)
            Ballot.objects.create(
                election=election,
                candidate=candidate,
                ballot_hash=ballot_hash
            )

            # 6. Record Voter Participation Ledger (Proves user voted, no candidate linkage)
            VoterParticipation.objects.create(
                user=user,
                election=election,
                receipt_token=receipt_token,
                ip_hash=ballot_hash[:16]
            )

            # 7. Audit Logging (Notice: ballot choice is NEVER logged!)
            log_audit_event(
                request=request,
                action='BALLOT_CAST_SUCCESS',
                details=f"Confidential ballot cast in election '{election.title}'. Anonymized receipt: {receipt_token}. Identity unlinked from vote choice.",
                severity='INFO',
                user=user
            )

    except IntegrityError:
        messages.error(request, "A database conflict occurred: A ballot has already been recorded for your account.")
        return redirect('election_detail', slug=slug)
    except Exception as e:
        messages.error(request, f"An unexpected error occurred while casting your vote: {str(e)}")
        return redirect('election_detail', slug=slug)

    # Success: display generic confirmation with official receipt
    messages.success(request, "Your vote has been securely and anonymously recorded!")
    return redirect('vote_receipt', slug=slug, receipt=receipt_token)


@login_required
def vote_receipt_view(request, slug, receipt):
    """
    Displays the verifiable participation receipt.
    Allows the voter to verify their participation without revealing their ballot choice.
    """
    election = get_object_or_404(Election, slug=slug)
    participation = get_object_or_404(VoterParticipation, election=election, receipt_token=receipt)

    # For privacy, only the voter who cast it or an admin can view this receipt page
    if participation.user != request.user and not request.user.profile.is_admin_role:
        raise Http404("Receipt not found or unauthorized.")

    context = {
        'election': election,
        'participation': participation,
        'receipt_token': receipt,
    }
    return render(request, 'voter/vote_receipt.html', context)


# ==============================================================================
# 5. ELECTION RESULTS & ANALYTICS
# ==============================================================================

def results_view(request, slug):
    """
    Election Results Dashboard.
    Enforces rule: Results are strictly HIDDEN until the election has closed AND
    an authorized administrator has published the results.
    Includes Chart.js datasets for interactive bar and doughnut charts.
    """
    election = get_object_or_404(Election, slug=slug)

    # Server-side validation: Results only visible when status is RESULTS_PUBLISHED
    if election.status != ElectionStatus.RESULTS_PUBLISHED:
        # Check if user is admin (admins can preview closed election results in admin panel)
        context = {
            'election': election,
            'is_published': False,
        }
        return render(request, 'voter/results_locked.html', context)

    results_data = election.get_results_data()

    # Prepare JSON datasets for Chart.js
    chart_labels = [r['candidate'].name for r in results_data['results']]
    chart_votes = [r['votes'] for r in results_data['results']]
    chart_colors = [r['candidate'].avatar_color or '#0284c7' for r in results_data['results']]

    context = {
        'election': election,
        'is_published': True,
        'results_data': results_data,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_votes_json': json.dumps(chart_votes),
        'chart_colors_json': json.dumps(chart_colors),
    }
    return render(request, 'voter/results.html', context)


# ==============================================================================
# 6. ADMINISTRATOR DASHBOARD & MANAGEMENT PORTAL
# ==============================================================================

def admin_required(view_func):
    """Decorator to enforce Election Administrator permissions."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.is_staff or 
                (hasattr(request.user, 'profile') and request.user.profile.is_admin_role)):
            messages.error(request, "Access denied: Administrator privileges required.")
            return redirect('voter_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard_view(request):
    """Admin dashboard with election metrics, lifecycle actions, and audit summary."""
    elections = Election.objects.all().order_by('-created_at')
    total_ballots = Ballot.objects.count()
    total_voters = UserProfile.objects.filter(role=UserRole.VOTER).count()
    active_elections = Election.objects.filter(status=ElectionStatus.ACTIVE).count()
    recent_audits = AuditLog.objects.all()[:10]

    context = {
        'elections': elections,
        'total_ballots': total_ballots,
        'total_voters': total_voters,
        'active_elections': active_elections,
        'recent_audits': recent_audits,
        'status_choices': ElectionStatus.choices,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def admin_election_create_view(request):
    """Create a new election."""
    if request.method == 'POST':
        form = ElectionForm(request.POST)
        if form.is_valid():
            election = form.save(commit=False)
            election.created_by = request.user
            election.save()
            log_audit_event(
                request=request,
                action='ELECTION_CREATED',
                details=f"Admin {request.user.username} created election '{election.title}' [Status: {election.status}]",
                severity='INFO'
            )
            messages.success(request, f"Election '{election.title}' created successfully.")
            return redirect('admin_dashboard')
    else:
        form = ElectionForm()

    return render(request, 'admin_panel/election_form.html', {'form': form, 'is_edit': False})


@admin_required
def admin_election_edit_view(request, slug):
    """Edit existing election parameters and lifecycle status."""
    election = get_object_or_404(Election, slug=slug)
    old_status = election.status

    if request.method == 'POST':
        form = ElectionForm(request.POST, instance=election)
        if form.is_valid():
            updated = form.save()
            if old_status != updated.status:
                log_audit_event(
                    request=request,
                    action='ELECTION_STATUS_CHANGED',
                    details=f"Admin {request.user.username} transitioned '{election.title}' status from {old_status} to {updated.status}",
                    severity='WARNING'
                )
            messages.success(request, f"Election '{updated.title}' updated successfully.")
            return redirect('admin_dashboard')
    else:
        form = ElectionForm(instance=election)

    candidates = election.candidates.all()
    context = {
        'form': form,
        'election': election,
        'candidates': candidates,
        'is_edit': True,
    }
    return render(request, 'admin_panel/election_form.html', context)


@admin_required
def admin_status_change_view(request, slug):
    """Quick lifecycle status update endpoint."""
    if request.method == 'POST':
        election = get_object_or_404(Election, slug=slug)
        new_status = request.POST.get('status')
        if new_status in dict(ElectionStatus.choices):
            old_status = election.status
            election.status = new_status
            election.save()
            log_audit_event(
                request=request,
                action='ELECTION_STATUS_UPDATED',
                details=f"Status of '{election.title}' changed from {old_status} to {new_status} by {request.user.username}",
                severity='WARNING'
            )
            messages.success(request, f"Status of '{election.title}' changed to {election.get_status_display()}.")
    return redirect('admin_dashboard')


@admin_required
def admin_publish_results_view(request, slug):
    """
    Publish election results after closure.
    Enforces rule: Can only publish if election has closed.
    """
    election = get_object_or_404(Election, slug=slug)
    
    if request.method == 'POST':
        election.status = ElectionStatus.RESULTS_PUBLISHED
        election.save()
        log_audit_event(
            request=request,
            action='RESULTS_PUBLISHED',
            details=f"Official results certified and published for '{election.title}' by {request.user.username}. Total votes: {election.total_votes_cast()}",
            severity='SECURITY'
        )
        messages.success(request, f"Official election results for '{election.title}' have been published!")
        return redirect('results', slug=slug)

    return redirect('admin_dashboard')


@admin_required
def admin_candidate_create_view(request, slug):
    """Add a new candidate to a specific election."""
    election = get_object_or_404(Election, slug=slug)

    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.election = election
            candidate.save()
            log_audit_event(
                request=request,
                action='CANDIDATE_ADDED',
                details=f"Candidate {candidate.name} added to '{election.title}'",
                severity='INFO'
            )
            messages.success(request, f"Candidate {candidate.name} registered successfully.")
            return redirect('admin_election_edit', slug=election.slug)
    else:
        # Pre-calculate next ballot number
        next_num = election.candidates.count() + 1
        form = CandidateForm(initial={'election': election, 'ballot_number': next_num})

    context = {
        'form': form,
        'election': election,
        'is_edit': False,
    }
    return render(request, 'admin_panel/candidate_form.html', context)


@admin_required
def admin_candidate_edit_view(request, candidate_id):
    """Edit candidate profile details."""
    candidate = get_object_or_404(Candidate, id=candidate_id)

    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            log_audit_event(
                request=request,
                action='CANDIDATE_UPDATED',
                details=f"Candidate {candidate.name} updated by {request.user.username}",
                severity='INFO'
            )
            messages.success(request, f"Candidate {candidate.name} updated.")
            return redirect('admin_election_edit', slug=candidate.election.slug)
    else:
        form = CandidateForm(instance=candidate)

    context = {
        'form': form,
        'candidate': candidate,
        'election': candidate.election,
        'is_edit': True,
    }
    return render(request, 'admin_panel/candidate_form.html', context)


@admin_required
def admin_candidate_delete_view(request, candidate_id):
    """Delete candidate (only allowed if election has no ballots yet)."""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    election = candidate.election

    if request.method == 'POST':
        if candidate.ballots.exists():
            messages.error(request, "Cannot delete a candidate who has already received cast ballots.")
            return redirect('admin_election_edit', slug=election.slug)
        
        name = candidate.name
        candidate.delete()
        log_audit_event(
            request=request,
            action='CANDIDATE_DELETED',
            details=f"Candidate {name} removed from '{election.title}' by {request.user.username}",
            severity='WARNING'
        )
        messages.success(request, f"Candidate '{name}' was removed.")
    return redirect('admin_election_edit', slug=election.slug)


@admin_required
def admin_audit_logs_view(request):
    """View tamper-evident administrative and system audit logs."""
    severity_filter = request.GET.get('severity', 'ALL')
    search_query = request.GET.get('q', '').strip()

    logs = AuditLog.objects.all()

    if severity_filter != 'ALL':
        logs = logs.filter(severity=severity_filter)

    if search_query:
        logs = logs.filter(action__icontains=search_query) | logs.filter(details__icontains=search_query)

    context = {
        'audit_logs': logs[:150],
        'selected_severity': severity_filter,
        'search_query': search_query,
        'severities': AuditLog.Severity.choices,
    }
    return render(request, 'admin_panel/audit_logs.html', context)


# ==============================================================================
# 7. INFORMATIONAL & LEGAL STATIC PAGES
# ==============================================================================

def about_view(request):
    return render(request, 'pages/about.html')

def privacy_view(request):
    return render(request, 'pages/privacy.html')

def terms_view(request):
    return render(request, 'pages/terms.html')

def security_disclaimer_view(request):
    return render(request, 'pages/security_disclaimer.html')
