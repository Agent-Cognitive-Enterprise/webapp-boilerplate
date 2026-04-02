from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4


PathFactory = Callable[[], str]
RequestKwargsFactory = Callable[[], dict[str, object]]


def empty_request_kwargs() -> dict[str, object]:
    return {}


def admin_settings_post_kwargs() -> dict[str, object]:
    return {"json": {}}


def user_detail_path() -> str:
    return f"/users/{uuid4()}"


def static_path(path: str) -> PathFactory:
    return lambda: path


ADMIN_USER_DETAIL_PATH_FACTORY = user_detail_path


@dataclass(frozen=True)
class ProtectedRouteProbeCase:
    case_id: str
    guard_path: str
    method: str
    path_factory: PathFactory
    request_kwargs_factory: RequestKwargsFactory
    needs_csrf_origin: bool = False


ADMIN_PROTECTED_ROUTE_PROBE_CASES = (
    ProtectedRouteProbeCase(
        case_id="admin-settings-get",
        guard_path="/admin/settings",
        method="get",
        path_factory=static_path("/admin/settings"),
        request_kwargs_factory=empty_request_kwargs,
    ),
    ProtectedRouteProbeCase(
        case_id="admin-settings-post",
        guard_path="/admin/settings",
        method="post",
        path_factory=static_path("/admin/settings"),
        request_kwargs_factory=admin_settings_post_kwargs,
        needs_csrf_origin=True,
    ),
    ProtectedRouteProbeCase(
        case_id="admin-settings-email-check-get",
        guard_path="/admin/settings/email/check",
        method="get",
        path_factory=static_path("/admin/settings/email/check"),
        request_kwargs_factory=empty_request_kwargs,
    ),
    ProtectedRouteProbeCase(
        case_id="users-list-get",
        guard_path="/users",
        method="get",
        path_factory=static_path("/users"),
        request_kwargs_factory=empty_request_kwargs,
    ),
    ProtectedRouteProbeCase(
        case_id="users-detail-get",
        guard_path="/users/{id}",
        method="get",
        path_factory=ADMIN_USER_DETAIL_PATH_FACTORY,
        request_kwargs_factory=empty_request_kwargs,
    ),
)

ADMIN_GET_PROBE_PATH_FACTORIES = tuple(
    case.path_factory
    for case in ADMIN_PROTECTED_ROUTE_PROBE_CASES
    if case.method == "get"
)
USER_AUTH_REQUIRED_GET_PATHS = ("/users/me/",)
USER_METHOD_DISCLOSURE_PATHS = ("/user-settings",)
