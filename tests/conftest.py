import os


def _sanitize_sops_env():
    """Override SOPS-encrypted env values with safe test defaults.

    fastmcp.Settings (pydantic_settings with env_file=".env") reads LOG_LEVEL
    from the .env file during ``import fastmcp``.  SOPS-encrypted values like
    ``ENC[AES256_GCM,...]`` fail its strict ``Literal`` validation.

    Setting FASTMCP_LOG_LEVEL in os.environ takes priority over the dotenv
    source (env vars > env_file in pydantic_settings) and prevents the crash.

    This only overrides values that look SOPS-encrypted or are missing, so it
    won't interfere with tests that set their own env vars.
    """
    sops_defaults = {
        "FASTMCP_LOG_LEVEL": "INFO",
        "LOG_LEVEL": "INFO",
        "DOLIBARR_URL": "https://test.example.com/api/index.php",
        "DOLIBARR_API_KEY": "test_api_key_for_testing",
    }
    for key, default in sops_defaults.items():
        val = os.environ.get(key, "")
        if val.startswith("ENC["):
            os.environ[key] = default

    # FASTMCP_LOG_LEVEL must always be set so fastmcp import succeeds
    # (the .env file's LOG_LEVEL may be encrypted even if the env var is not)
    if "FASTMCP_LOG_LEVEL" not in os.environ:
        os.environ["FASTMCP_LOG_LEVEL"] = "INFO"


_sanitize_sops_env()
