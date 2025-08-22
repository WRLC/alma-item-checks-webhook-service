"""Test configurations"""
import pytest
import importlib

# Import the module to be tested
from alma_item_checks_webhook_service import config


@pytest.fixture
def base_env():
    """Provides the minimum required environment variables for the config module to load."""
    return {
        "AzureWebJobsStorage": "test_storage_connection",
        "SQLALCHEMY_CONNECTION_STRING": "test_db_connection",
        "WEBHOOK_SECRET": "test_webhook_secret",
    }


def test_get_required_env_variable_found(mocker):
    """Test that _get_required_env returns the value if the env var exists."""
    mocker.patch.dict('os.environ', {'TEST_VAR': 'test_value'})
    assert config._get_required_env('TEST_VAR') == 'test_value'


def test_get_required_env_variable_missing(mocker):
    """Test that _get_required_env raises a ValueError if the env var is missing."""
    mocker.patch.dict('os.environ', {}, clear=True)
    with pytest.raises(ValueError, match="Missing required environment variable: 'MISSING_VAR'"):
        config._get_required_env('MISSING_VAR')


@pytest.mark.parametrize(
    "env_var, set_value, expected_value, default_value",
    [
        ("FETCH_ITEM_QUEUE", "custom-queue", "custom-queue", "fetch-item-queue"),
    ]
)
def test_optional_env_variables(mocker, base_env, env_var, set_value, expected_value, default_value):
    """Test optional environment variables with and without values set."""
    # Test with the environment variable set
    env_with_optional = base_env.copy()
    env_with_optional[env_var] = set_value
    mocker.patch.dict('os.environ', env_with_optional, clear=True)
    importlib.reload(config)
    assert getattr(config, env_var) == expected_value

    # Test with the environment variable not set (should use default)
    mocker.patch.dict('os.environ', base_env, clear=True)
    importlib.reload(config)
    assert getattr(config, env_var) == default_value


def test_required_env_variables_loaded(mocker, base_env):
    """Test that required environment variables are correctly loaded."""
    mocker.patch.dict('os.environ', base_env, clear=True)
    importlib.reload(config)

    assert config.STORAGE_CONNECTION_STRING == base_env["AzureWebJobsStorage"]
    assert config.WEBHOOK_SECRET == base_env["WEBHOOK_SECRET"]
