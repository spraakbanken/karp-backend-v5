from flask_matomo2 import Matomo
from karp5.config import conf_mgr

matomo = Matomo(
    matomo_url=conf_mgr.app_config.TRACKING_MATOMO_URL or "NOT_USED",
    id_site=conf_mgr.app_config.TRACKING_SITE_ID or -1,
    token_auth=conf_mgr.app_config.TRACKING_AUTH_TOKEN,
    base_url=conf_mgr.app_config.BACKEND_URL,
)
