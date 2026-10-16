from django.utils import timezone
from .models import Election, ElectionStatus, UserRole


def ballotbridge_context(request):
    """Provides platform brand identity and quick stats to all templates."""
    active_count = Election.objects.filter(status=ElectionStatus.ACTIVE).count()
    user_profile = None
    is_admin_user = False

    if request.user.is_authenticated:
        user_profile = getattr(request.user, 'profile', None)
        if user_profile and user_profile.is_admin_role:
            is_admin_user = True
        elif request.user.is_superuser or request.user.is_staff:
            is_admin_user = True

    return {
        'APP_NAME': 'BallotBridge',
        'APP_TAGLINE': 'Your Voice. Your Choice. Your Future.',
        'ACTIVE_ELECTIONS_COUNT': active_count,
        'CURRENT_USER_PROFILE': user_profile,
        'IS_ADMIN_USER': is_admin_user,
        'CURRENT_YEAR': timezone.now().year,
    }
