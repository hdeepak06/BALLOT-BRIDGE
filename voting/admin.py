from django.contrib import admin
from .models import UserProfile, Election, Candidate, Ballot, VoterParticipation, AuditLog, Announcement


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'voter_id', 'organization', 'department', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified', 'organization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'voter_id')


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1
    fields = ('ballot_number', 'name', 'role_title', 'party_or_slate')


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'start_time', 'end_time', 'eligibility_criteria', 'is_featured')
    list_filter = ('status', 'category', 'eligibility_criteria', 'is_featured')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CandidateInline]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'election', 'ballot_number', 'party_or_slate', 'role_title')
    list_filter = ('election', 'party_or_slate')
    search_fields = ('name', 'manifesto', 'short_bio')


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    list_display = ('ballot_hash_preview', 'election', 'candidate', 'cast_at')
    list_filter = ('election', 'cast_at')
    readonly_fields = ('ballot_hash', 'election', 'candidate', 'cast_at')

    def ballot_hash_preview(self, obj):
        return f"{obj.ballot_hash[:16]}..."
    ballot_hash_preview.short_description = "Encrypted Ballot Hash"

    def has_add_permission(self, request):
        return False


@admin.register(VoterParticipation)
class VoterParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'election', 'receipt_preview', 'voted_at')
    list_filter = ('election', 'voted_at')
    search_fields = ('user__username', 'receipt_token')
    readonly_fields = ('user', 'election', 'receipt_token', 'ip_hash', 'voted_at')

    def receipt_preview(self, obj):
        return f"{obj.receipt_token[:16]}..."
    receipt_preview.short_description = "Voter Receipt Token"

    def has_add_permission(self, request):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'severity', 'user', 'action', 'ip_address')
    list_filter = ('severity', 'action', 'timestamp')
    search_fields = ('action', 'details', 'user__username')
    readonly_fields = ('timestamp', 'user', 'action', 'details', 'ip_address', 'severity')

    def has_add_permission(self, request):
        return False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'election', 'is_pinned', 'created_at')
    list_filter = ('is_pinned', 'created_at')
    search_fields = ('title', 'message')
