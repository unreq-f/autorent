from core.models import Booking, Fine, ContactMessage

def manager_context(request):
    """Add manager sidebar counts to all manager templates"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return {}
    return {
        'pending_count': Booking.objects.filter(status='pending').count(),
        'unpaid_fines':  Fine.objects.filter(status='unpaid').count(),
        'new_inquiries': ContactMessage.objects.filter(status='new').count(),
    }