from django.conf import settings

def fundraising_campaign(request):
    return {
        "fundraiser_enabled": getattr(settings, "FUNDRAISER_ENABLED", False),
        "fundraiser_campaign_id": getattr(settings, "FUNDRAISER_CAMPAIGN_ID", None),
    }
