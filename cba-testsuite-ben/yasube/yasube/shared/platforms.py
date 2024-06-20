from enum import Enum
from typing import TypedDict, Union

import prefect
import requests
from oauthlib.oauth2 import BackendApplicationClient, LegacyApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from typing_extensions import NotRequired


class AuthType(Enum):
    BASIC = "basic"
    OAUTH = "oauth"


class OAuthGrantType(Enum):
    CODE = "code"
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "client_credentials"


class BasicAuthCredentials(TypedDict):
    username: str
    password: str


class OAuthCredentials(BasicAuthCredentials):
    client_id: str
    client_secret: str
    token_url: str
    grant_type: str
    token_requires_scope: NotRequired[bool]


class Auth(TypedDict):
    type: AuthType
    credentials: Union[BasicAuthCredentials, OAuthCredentials]


class TrustedRedirectMixin:
    def rebuild_auth(self, prepared_request, response):
        """The original implementation tries to strip the
        authentication to avoid credentials leaking.
        An empty implementation should simulate the
        curl --location-trusted behavior.
        """
        logger = prefect.context.get("logger")
        logger.info(
            f"Redirecting to {prepared_request.url} from {response.request.url}"
        )


class TrustedRedirectBasicSession(TrustedRedirectMixin, requests.Session):
    """Keeps authorization across redirects in basic sessions"""


class TrustedRedirectOAuth2Session(TrustedRedirectMixin, OAuth2Session):
    """Keeps authorization across redirects in oauth sessions"""


class Platform:
    def __init__(
        self,
        key: str,
        label: str,
        root_uri: str,
        auth: Auth,
        num_workers=1,
        verify_ssl=True,
        location_trusted=False,
    ):
        self.key = key
        self.label = label
        self.root_uri = root_uri
        self.auth = auth
        self.num_workers = num_workers
        self.verify_ssl = verify_ssl
        self.location_trusted = location_trusted
        self._session = None

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            if self.auth["type"] == AuthType.BASIC.value:
                self._session = self._get_basic_auth_session()
            elif self.auth["type"] == AuthType.OAUTH.value:
                self._session = self._get_oauth_session()

        return self._session

    def _token_saver(self, token):
        self._token = token

    def _get_basic_auth_session(self) -> requests.Session:
        if self.location_trusted:
            session_class = TrustedRedirectBasicSession
        else:
            session_class = requests.Session

        session = session_class()
        session.auth = HTTPBasicAuth(
            self.auth["credentials"]["username"],
            self.auth["credentials"]["password"],
        )
        return session

    def _get_oauth_session(self) -> requests.Session:
        if self.location_trusted:
            session_class = TrustedRedirectOAuth2Session
        else:
            session_class = OAuth2Session

        credentials = self.auth["credentials"]
        if credentials["grant_type"] == OAuthGrantType.PASSWORD.value:
            oauth = session_class(
                client=LegacyApplicationClient(client_id=credentials["client_id"])
            )
            kwargs = {}
            if credentials.get("token_requires_scope", False):
                kwargs["scope"] = credentials.get("scope", "")

            token = oauth.fetch_token(
                token_url=credentials["token_url"],
                username=credentials["username"],
                password=credentials["password"],
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                **kwargs,
            )
        elif credentials["grant_type"] in (
            OAuthGrantType.CODE.value,
            OAuthGrantType.CLIENT_CREDENTIALS.value,
        ):
            client = BackendApplicationClient(client_id=credentials["client_id"])
            oauth = session_class(client=client)
            token = oauth.fetch_token(
                token_url=credentials["token_url"],
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
            )
        return session_class(
            client_id=credentials["client_id"],
            token=token,
            auto_refresh_url=credentials["token_url"],
            token_updater=self._token_saver,
        )
