import os
from enum import Enum

from google.auth import default, impersonated_credentials, transport
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_plugins import dwd_credentials


class AuthType(Enum):
    ADC = 1
    DWD = 2
    OAUTH2 = 3


def get_credentials(service, *args, **kwargs) -> Credentials:
    """
    Obtains user credentials for accessing a service based on the authentication type.
    """
    match service.auth_type:
        case AuthType.ADC:
            return __get_adc_credentials(*args, **kwargs)
        case AuthType.DWD:
            return __get_dwd_credentials(service, *args, **kwargs)
        case AuthType.OAUTH2:
            return __get_oauth_credentials(service, *args, **kwargs)
        case _:
            raise ValueError(f"Authentication type not currently managed: {service.auth_type}")


def __get_adc_credentials() -> Credentials:
    """
    Remember to pass scopes when logging with ADC
    Ex: gcloud auth application-default login --scopes="https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/cloud-platform"
    """
    credentials, _ = default()
    if credentials.expired or not credentials.valid:
        credentials.refresh(transport.requests.Request())
    return credentials


def __get_dwd_credentials(
    service, user_email=None, service_account_email=None, service_account_file=None
) -> Credentials:
    """
    Impersonate service account to access a specific service
    Requires Service Account Token Creator on the ADC's account owner

    service_account_file SHOULD NOT BE USED if possible
    """

    if not service_account_email and not service_account_file:
        raise ValueError("Missing SA Identity, can't proceed DWD")

    # Get from SA key
    if service_account_file:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=service.scopes
        )
        return credentials.with_subject(user_email)

    if service_account_email:
        # Impersonate specified user without the need of Service Account key
        if user_email:
            # If user email is specified, will use this identity
            return dwd_credentials.Credentials(
                subject=user_email,
                source_credentials=__get_adc_credentials(),
                target_principal=service_account_email,
                target_scopes=service.scopes,
            )
        else:
            # If user not specified, will use SA's identity
            return impersonated_credentials.Credentials(
                source_credentials=__get_adc_credentials(),
                target_principal=service_account_email,
                target_scopes=service.scopes,
            )


def __get_oauth_credentials(
    service, oauth2_client="credentials.json", token_file="token.json", needs_refresh=False
) -> Credentials:
    """
    Server to Server usage
    Uses OAuth client to prompt user and obtain credentials
    Stores the credentials locally
    """
    creds = None
    if needs_refresh:
        os.remove(token_file)
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, service.scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(oauth2_client, service.scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return creds
