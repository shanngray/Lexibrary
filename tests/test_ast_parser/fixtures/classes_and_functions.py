"""Module with classes, methods, and various decorator patterns."""

API_VERSION = "2.0"
base_url: str = "https://api.example.com"


class BaseService:
    """Base class for all services."""

    timeout: int = 30

    def __init__(self, name: str, config: dict | None = None) -> None:
        self.name = name
        self.config = config or {}

    def health_check(self) -> bool:
        """Check service health."""
        return True

    def _internal_setup(self) -> None:
        """Private setup method -- should be excluded."""
        pass

    def __repr__(self) -> str:
        """Repr -- should be excluded (dunder, not __init__/__new__)."""
        return f"BaseService({self.name!r})"


class AuthService(BaseService):
    """Authentication service with various method types."""

    max_attempts: int = 5

    def __init__(self, name: str, secret: str) -> None:
        super().__init__(name)
        self.secret = secret

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return password  # placeholder

    @classmethod
    def from_env(cls, env_prefix: str = "AUTH") -> "AuthService":
        """Create an AuthService from environment variables."""
        return cls(name="auth", secret="secret")

    @property
    def is_configured(self) -> bool:
        """Check if the service is configured."""
        return bool(self.secret)

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        return True

    async def authenticate_async(self, username: str, password: str) -> bool:
        """Async authentication."""
        return True


def create_service(service_type: str) -> BaseService:
    """Factory function."""
    return BaseService(name=service_type)


def _private_helper() -> None:
    """Should not appear in the interface."""
    pass
