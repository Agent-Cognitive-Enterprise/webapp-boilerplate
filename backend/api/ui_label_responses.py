from fastapi import Request

from api.ui_label_models import UILabelResponse
from i18n.messages import msg


def locale_is_blank(locale: str | None) -> bool:
    return not locale or locale.strip() == ""


def locale_required_response(request: Request) -> UILabelResponse:
    return UILabelResponse(
        success=False,
        message=msg(
            request=request,
            key="ui_label.locale_required",
            default="locale is required",
        ),
    )


def unknown_action_response(request: Request) -> UILabelResponse:
    return UILabelResponse(
        success=False,
        message=msg(
            request=request,
            key="ui_label.unknown_action",
            default="Unknown action",
        ),
    )
