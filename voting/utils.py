import hashlib
import secrets
import uuid
from .models import AuditLog


def get_client_ip(request):
    """Retrieve client IP address from request headers."""
    if not request:
        return '127.0.0.1'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def log_audit_event(request=None, action="", details="", severity='INFO', user=None):
    """
    Record administrative and critical security events without ever logging
    ballot choices alongside voter identity.
    """
    actual_user = user
    if actual_user is None and request and hasattr(request, 'user') and request.user.is_authenticated:
        actual_user = request.user
    
    ip = get_client_ip(request) if request else '127.0.0.1'
    
    AuditLog.objects.create(
        user=actual_user,
        action=action,
        details=details,
        ip_address=ip,
        severity=severity
    )


def generate_voter_id():
    """Generates a professional voter identifier like BB-78429."""
    token = secrets.randbelow(90000) + 10000
    return f"BB-2026-{token}"


def generate_ballot_hash(election_id, candidate_id):
    """
    Generates a secure SHA-256 cryptographic hash for an anonymous ballot record.
    The voter identity is intentionally absent from this hash.
    """
    entropy = f"{uuid.uuid4().hex}:{election_id}:{candidate_id}:{secrets.token_hex(16)}"
    return hashlib.sha256(entropy.encode('utf-8')).hexdigest()


def generate_receipt_token(user_id, election_id):
    """
    Generates a verification receipt token that the voter can retain to verify their
    participation was registered in the turnout ledger without revealing their candidate.
    """
    raw_str = f"{user_id}:{election_id}:{uuid.uuid4().hex}:{secrets.token_hex(8)}"
    digest = hashlib.sha256(raw_str.encode('utf-8')).hexdigest().upper()
    return f"BB-REC-{digest[:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"
