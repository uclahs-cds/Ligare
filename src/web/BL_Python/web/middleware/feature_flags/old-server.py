"""
Server blueprint
Non-API specific endpoints for application management
"""

from typing import Any, Sequence, cast

import flask
from BL_Python.platform.feature_flag import FeatureFlagChange, FeatureFlagRouter
from BL_Python.platform.feature_flag.db_feature_flag_router import (
    FeatureFlag as DBFeatureFlag,
)
from BL_Python.web.middleware.sso import login_required
from flask import request
from injector import inject

from CAP import __version__
from CAP.app.models.user.role import Role as UserRole
from CAP.app.schemas.platform.get_request_feature_flag_schema import (
    GetResponseFeatureFlagSchema,
)
from CAP.app.schemas.platform.patch_request_feature_flag_schema import (
    PatchRequestFeatureFlag,
    PatchRequestFeatureFlagSchema,
    PatchResponseFeatureFlagSchema,
)
from CAP.app.schemas.platform.response_problem_schema import (
    ResponseProblem,
    ResponseProblemSchema,
)

_FEATURE_FLAG_NOT_FOUND_PROBLEM_TITLE = "Feature Flag Not Found"
_FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS = 404


def healthcheck():
    return "healthcheck: flask app is running"


@login_required([UserRole.Administrator])
def server_meta():
    return {"CAP": {"version": __version__}}


# @server_blueprint.route("/server/feature_flag", methods=("GET",))
@login_required([UserRole.Operator])
@inject
def feature_flag(feature_flag_router: FeatureFlagRouter[DBFeatureFlag]):
    request_query_names: list[str] | None = request.args.to_dict(flat=False).get("name")

    feature_flags: Sequence[DBFeatureFlag]
    missing_flags: set[str] | None = None
    if request_query_names is None:
        feature_flags = feature_flag_router.get_feature_flags()
    elif isinstance(
        request_query_names, list
    ):  # pyright: ignore[reportUnnecessaryIsInstance]
        feature_flags = feature_flag_router.get_feature_flags(request_query_names)
        missing_flags = set(request_query_names).difference(
            set([feature_flag.name for feature_flag in feature_flags])
        )
    else:
        raise ValueError("Unexpected type from Flask query parameters.")

    response: dict[str, Any] = {}

    if missing_flags:
        problems: list[ResponseProblem] = []
        for missing_flag in missing_flags:
            problems.append(
                ResponseProblem(
                    title=_FEATURE_FLAG_NOT_FOUND_PROBLEM_TITLE,
                    detail="Queried feature flag does not exist.",
                    instance=missing_flag,
                    status=_FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS,
                    type=None,
                )
            )
        response["problems"] = ResponseProblemSchema().dump(problems, many=True)

    if feature_flags:
        response["data"] = GetResponseFeatureFlagSchema().dump(feature_flags, many=True)
        return response
    else:
        return response, _FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS


# @server_blueprint.route("/server/feature_flag", methods=("PATCH",))
@login_required([UserRole.Operator])
@inject
def feature_flag_patch(feature_flag_router: FeatureFlagRouter[DBFeatureFlag]):
    post_request_feature_flag_schema = PatchRequestFeatureFlagSchema()

    feature_flags: list[PatchRequestFeatureFlag] = cast(
        list[PatchRequestFeatureFlag],
        post_request_feature_flag_schema.load(
            flask.request.json,  # pyright: ignore[reportArgumentType] why is `flask.request.json` wrong here?
            many=True,
        ),
    )

    changes: list[FeatureFlagChange] = []
    problems: list[ResponseProblem] = []
    for flag in feature_flags:
        try:
            change = feature_flag_router.set_feature_is_enabled(flag.name, flag.enabled)
            changes.append(change)
        except LookupError:
            problems.append(
                ResponseProblem(
                    title=_FEATURE_FLAG_NOT_FOUND_PROBLEM_TITLE,
                    detail="Feature flag to PATCH does not exist. It must be created first.",
                    instance=flag.name,
                    status=_FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS,
                    type=None,
                )
            )

    response: dict[str, Any] = {}

    if problems:
        response["problems"] = ResponseProblemSchema().dump(problems, many=True)

    if changes:
        response["data"] = PatchResponseFeatureFlagSchema().dump(changes, many=True)
        return response
    else:
        return response, _FEATURE_FLAG_NOT_FOUND_PROBLEM_STATUS
