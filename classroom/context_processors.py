from .models import SystemConfig

def site_branding(request):
    """
    Makes branding settings available in all templates globally.
    """
    return {'branding': SystemConfig.get_config()}