## GitLab configuration settings

external_url 'https://test-minimetis.dev/gitlab/'
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
      'issuer' => 'https://test-minimetis.dev/keycloak/auth/realms/metis',
      'discovery' => true,
      'client_auth_method' => 'query',
      'uid_field' => 'preferred_username',
      'send_scope_to_token_endpoint' => 'false',
      'client_options' => {
        'scheme' => 'http',
        'identifier' => 'gitlab',
        'secret' => '946c0b69-d73c-4aaa-a8fc-a26d4cde6592',
        'redirect_uri' => 'https://test-minimetis.dev/gitlab//users/auth/openid_connect/callback'
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

