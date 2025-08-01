"""Configuration générale de l'application"""

APP_CONFIG = {
    "page_title": "📊 Mon App Analytics Pro",
    "page_icon": "🚀",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

AUTH_ACTIONS = [
    'login', 'register', 'forgot_password',
    'reset_password', 'update_user_details'
]

DATABASE_CONFIG = {
    "url": "sqlite:///app_database.db",
    "echo": False
}

# Categories par défaut
DEFAULT_CATEGORIES = [
    "Personnel", "Travail", "Projet", "Idée",
    "Note", "Formation", "Recherche", "Autre"
]

# Priorités disponibles
PRIORITY_OPTIONS = ["High", "Medium", "Low"]

# Statuts disponibles
STATUS_OPTIONS = ["Active", "Completed", "Paused", "Cancelled"]
