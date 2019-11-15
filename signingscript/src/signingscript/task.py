#!/usr/bin/env python
"""Signingscript task functions.

Attributes:
    FORMAT_TO_SIGNING_FUNCTION (frozendict): a mapping between signing format
        and signing function. If not specified, use the `default` signing
        function.

"""
from frozendict import frozendict
import logging
import os
import re

from scriptworker.exceptions import TaskVerificationError
from scriptworker.utils import get_single_item_from_sequence

import signingscript.sign as ssign
from signingscript.sign import (
    sign_gpg,
    sign_jar,
    sign_macapp,
    sign_widevine,
    sign_file,
    sign_mar384_with_autograph_hash,
    sign_gpg_with_autograph,
    sign_omnija,
    sign_langpack,
    sign_authenticode_zip,
    extract_archive,
)

log = logging.getLogger(__name__)

FORMAT_TO_SIGNING_FUNCTION = frozendict(
    {
        # TODO: Remove the next item (in favor of the regex one), once Focus is migrated
        "autograph_focus": sign_jar,
        "autograph_apk_.+": sign_jar,
        "autograph_hash_only_mar384(:\\w+)?": sign_mar384_with_autograph_hash,
        "autograph_stage_mar384(:\\w+)?": sign_mar384_with_autograph_hash,
        "gpg": sign_gpg,
        "autograph_gpg": sign_gpg_with_autograph,
        "jar": sign_jar,
        "focus-jar": sign_jar,
        "macapp": sign_macapp,
        "widevine": sign_widevine,
        "autograph_widevine": sign_widevine,
        "autograph_omnija": sign_omnija,
        "autograph_langpack": sign_langpack,
        "autograph_authenticode": sign_authenticode_zip,
        "autograph_authenticode_stub": sign_authenticode_zip,
        "default": sign_file,
    }
)


# task_cert_type {{{1
def task_cert_type(context):
    """Extract task certificate type.

    Args:
        context (Context): the signing context.

    Raises:
        TaskVerificationError: if the number of cert scopes is not 1.

    Returns:
        str: the cert type.

    """
    if not context.task or not context.task["scopes"]:
        raise TaskVerificationError("No scopes found")

    prefixes = _get_cert_prefixes(context)
    scopes = _extract_scopes_from_unique_prefix(
        scopes=context.task["scopes"], prefixes=prefixes
    )
    return get_single_item_from_sequence(
        scopes,
        condition=lambda _: True,  # scopes must just contain 1 single item
        ErrorClass=TaskVerificationError,
        no_item_error_message="No scope starting with any of these prefixes {} found".format(
            prefixes
        ),
        too_many_item_error_message="More than one scope found",
    )


# task_signing_formats {{{1
def task_signing_formats(context):
    """Get the list of signing formats from the task payload.

    Args:
        context (Context): the signing context.

    Returns:
        set: the signing formats.

    """
    formats = set()
    for u in context.task.get("payload", {}).get("upstreamArtifacts", []):
        formats.update(u["formats"])
    return formats


def _extract_scopes_from_unique_prefix(scopes, prefixes):
    scopes = [
        scope for scope in scopes for prefix in prefixes if scope.startswith(prefix)
    ]
    _check_scopes_exist_and_all_have_the_same_prefix(scopes, prefixes)
    return scopes


def _get_cert_prefixes(context):
    return _get_scope_prefixes(context, "cert")


def _get_scope_prefixes(context, sub_namespace):
    prefixes = context.config["taskcluster_scope_prefixes"]
    prefixes = [
        prefix if prefix.endswith(":") else "{}:".format(prefix) for prefix in prefixes
    ]
    return ["{}{}:".format(prefix, sub_namespace) for prefix in prefixes]


def _check_scopes_exist_and_all_have_the_same_prefix(scopes, prefixes):
    for prefix in prefixes:
        if all(scope.startswith(prefix) for scope in scopes):
            break
    else:
        raise TaskVerificationError(
            "Scopes must exist and all have the same prefix. "
            "Given scopes: {}. Allowed prefixes: {}".format(scopes, prefixes)
        )


async def make_archive(context, dirname, archive_ext, output):
    """Create an archive."""
    files = ssign._get_files(dirname)
    if archive_ext == ".zip":
        output = await ssign._create_zipfile(context, output, files, dirname)
    elif archive_ext in (".tar.bz2", ".tar.gz"):
        compression = archive_ext.split(".")[-1]
        output = await ssign._create_tarfile(
            context, output, files, compression, dirname
        )
    else:
        raise ValueError("Unsupported archive format {}".format(archive_ext))
    return output


# sign {{{1
async def sign(context, path, signing_formats):
    """Call the appropriate signing function per format, for a single file.

    Args:
        context (Context): the signing context
        path (str): the source file to sign
        signing_formats (list): the formats to sign with

    Returns:
        list: the list of paths generated. This will be a list of one, unless
            there are detached sigfiles.

    """
    archive_formats = {
        "autograph_widevine",
        "autograph_omnija",
        "autograph_authenticode",
    }

    output = path
    recreate_archive = False
    if path.endswith(".zip"):
        archive_ext = ".zip"
    elif path.endswith(".tar.gz"):
        archive_ext = ".tar.gz"
    elif path.endswith(".tar.bz2"):
        archive_ext = ".tar.bz2"
    else:
        archive_ext = None
    # Loop through the formats and sign one by one.
    for fmt in signing_formats:
        signing_func = _get_signing_function_from_format(fmt)
        if fmt in archive_formats:
            if not os.path.isdir(output):
                output = await extract_archive(context, output)
            recreate_archive = True
        else:
            if os.path.isdir(output):
                output = await make_archive(context, output, archive_ext, path)
            recreate_archive = False

        output = await signing_func(context, output, fmt)

    # Re-create an archive if necessary
    if recreate_archive:
        output = await make_archive(context, output, archive_ext, path)

    # We want to return a list
    if not isinstance(output, (tuple, list)):
        output = [output]
    return output


def _get_signing_function_from_format(format):
    try:
        _, signing_function = get_single_item_from_sequence(
            FORMAT_TO_SIGNING_FUNCTION.items(),
            condition=lambda item: re.match(item[0], format) is not None,
        )
        return signing_function
    except ValueError:
        # Regex may catch several candidate. If so, we fall back to the exact match.
        # If nothing matches, then we fall back to default
        return FORMAT_TO_SIGNING_FUNCTION.get(
            format, FORMAT_TO_SIGNING_FUNCTION["default"]
        )


# _sort_formats {{{1
def _sort_formats(formats):
    """Order the signing formats.

    Certain formats need to happen before or after others, e.g. gpg after
    any format that modifies the binary.

    Args:
        formats (list): the formats to order.

    Returns:
        list: the ordered formats.

    """
    # Widevine formats must be after other formats other than macapp; GPG must
    # be last.
    for fmt in (
        "widevine",
        "autograph_widevine",
        "autograph_omnija",
        "macapp",
        "gpg",
        "autograph_gpg",
    ):
        if fmt in formats:
            formats.remove(fmt)
            formats.append(fmt)
    return formats


# build_filelist_dict {{{1
def build_filelist_dict(context):
    """Build a dictionary of cot-downloaded paths and formats.

    Scriptworker will pre-download and pre-verify the `upstreamArtifacts`
    in our `work_dir`.  Let's build a dictionary of relative `path` to
    a dictionary of `full_path` and signing `formats`.

    Args:
        context (Context): the signing context

    Raises:
        TaskVerificationError: if the files don't exist on disk

    Returns:
        dict of dicts: the dictionary of relative `path` to a dictionary with
            `full_path` and a list of signing `formats`.

    """
    filelist_dict = {}
    messages = []
    for artifact_dict in context.task["payload"]["upstreamArtifacts"]:
        for path in artifact_dict["paths"]:
            full_path = os.path.join(
                context.config["work_dir"], "cot", artifact_dict["taskId"], path
            )
            if not os.path.exists(full_path):
                messages.append("{} doesn't exist!".format(full_path))
            filelist_dict[path] = {
                "full_path": full_path,
                "formats": _sort_formats(artifact_dict["formats"]),
            }
    if messages:
        raise TaskVerificationError(messages)
    return filelist_dict
