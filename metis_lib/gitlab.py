from typing import Optional
from metis_lib import service
from string import Template

config = """## GitLab configuration settings

external_url '${base_url}'
letsencrypt['enable'] = false

gitlab_rails['gitlab_root_email']="admin@metis.eu"
gitlab_rails['initial_root_password'] = ENV["METIS_ADMIN_PASSWORD"]


gitlab_rails['omniauth_providers'] = [
  { 'name' => 'openid_connect',
    'label' => 'Keycloak',
#    'icon' => '<custom_provider_icon>',
    'args' => {
      'name' => 'openid_connect',
      'scope' => ['openid','profile'],
      'response_type' => 'code',
      'issuer' => '${issuer_url}',
      'discovery' => true,
      'client_auth_method' => 'query',
      'uid_field' => 'preferred_username',
      'send_scope_to_token_endpoint' => 'false',
      'client_options' => {
        'scheme' => 'http',
        'identifier' => '${client_id}',
        'secret' => '${client_secret}',
        'redirect_uri' => '${base_url}/users/auth/openid_connect/callback'
      }
    }
  }
]

gitlab_rails['block_auto_created_users'] = true
gitlab_rails['omniauth_allow_single_sign_on'] = ['openid_connect']
gitlab_rails['omniauth_block_auto_created_users'] = false
gitlab_rails['omniauth_auto_link_user'] = ['openid_connect']
gitlab_rails['omniauth_sync_profile_from_provider'] = ['openid_connect']
gitlab_rails['omniauth_sync_profile_attributes'] = ['email', 'user_name','first_name', 'last_name']
gitlab_rails['omniauth_auto_sign_in_with_provider'] = 'openid_connect'

"""


class Gitlab:
    def __init__(self, gitlab_url: str, gitlab_rb_path: str) -> None:
        self.url = gitlab_url
        self.gitlab_rb_path = gitlab_rb_path

    def wait_ready(self, timeout: Optional[float] = None):
        service.wait_respond(f"{self.url}/", timeout=timeout)

    def configure_omiauth(
        self, oidc_client_id: str, oidc_client_secret: str, issuer_url: str
    ):
        tpl = Template(config)
        content = tpl.substitute(
            base_url=self.url,
            client_id=oidc_client_id,
            client_secret=oidc_client_secret,
            issuer_url=issuer_url,
        )
        with open(self.gitlab_rb_path, "w") as gitlab_rb:
            gitlab_rb.write(content)
