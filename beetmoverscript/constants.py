MIME_MAP = {
    '': 'text/plain',
    '.asc': 'text/plain',
    '.beet': 'text/plain',
    '.bundle': 'application/octet-stream',
    '.bz2': 'application/octet-stream',
    '.checksums': 'text/plain',
    '.dmg': 'application/x-iso9660-image',
    '.json': 'application/json',
    '.mar': 'application/octet-stream',
    '.xpi': 'application/x-xpinstall',
    '.apk': 'application/vnd.android.package-archive',
}

STAGE_PLATFORM_MAP = {
    'linux': 'linux-i686',
    'linux-devedition': 'linux-i686',
    # XXX: temp hack until we solve 1424482
    'linux-devedition-devedition': 'linux-i686',
    'linux64': 'linux-x86_64',
    'linux64-asan-reporter': 'linux-x86_64-asan-reporter',
    'linux64-devedition': 'linux-x86_64',
    # XXX: temp hack until we solve 1424482
    'linux64-devedition-devedition': 'linux-x86_64',
    'macosx64': 'mac',
    'macosx64-devedition': 'mac',
    # XXX: temp hack until we solve 1424482
    'macosx64-devedition-devedition': 'mac',
    'win32': 'win32',
    'win32-devedition': 'win32',
    # XXX: temp hack until we solve 1424482
    'win32-devedition-devedition': 'win32',
    'win64': 'win64',
    'win64-devedition': 'win64',
    # XXX: temp hack until we solve 1424482
    'win64-devedition-devedition': 'win64',
}

NORMALIZED_BALROG_PLATFORMS = {
    "linux-devedition": "linux",
    "linux-devedition-devedition": "linux",
    "linux64-devedition": "linux64",
    "linux64-devedition-devedition": "linux64",
    "macosx64-devedition": "macosx64",
    "macosx64-devedition-devedition": "macosx64",
    "win32-devedition": "win32",
    "win32-devedition-devedition": "win32",
    "win64-devedition": "win64",
    "win64-devedition-devedition": "win64",
}

NORMALIZED_FILENAME_PLATFORMS = NORMALIZED_BALROG_PLATFORMS.copy()
NORMALIZED_FILENAME_PLATFORMS.update({
    "android": "android-arm",
    "android-api-15": "android-arm",
    "android-api-15-old-id": "android-arm",
    "android-api-16": "android-arm",
    "android-api-16-old-id": "android-arm",
    "android-x86": "android-i386",
    "android-x86-old-id": "android-i386",
    "android-aarch64": "android-aarch64",
})

HASH_BLOCK_SIZE = 1024*1024

INITIAL_RELEASE_PROPS_FILE = "balrog_props.json"
# release buckets don't require a copy of the following artifacts
IGNORED_UPSTREAM_ARTIFACTS = ["balrog_props.json"]

RELEASE_BRANCHES = (
    'mozilla-central',
    'mozilla-beta',
    'mozilla-release',
    'mozilla-esr52'
)

RESTRICTED_BUCKET_PATHS = {
    'nightly': [
        'pub/mobile/nightly',
        'pub/firefox/nightly',
    ],
    'release': [
        'pub/devedition/candidates',
        'pub/devedition/releases',
        'pub/firefox/candidates',
        'pub/firefox/releases',
        'pub/mobile/candidates',
        'pub/mobile/releases',
    ],
    'dep': [
        'pub/devedition/candidates',
        'pub/devedition/releases',
        'pub/firefox/nightly',
        'pub/firefox/candidates',
        'pub/firefox/releases',
        'pub/mobile/nightly',
        'pub/mobile/candidates',
        'pub/mobile/releases',
    ]
}

# actions that imply actual releases, hence the need of `build_number` and
# `version`
PROMOTION_ACTIONS = (
    'push-to-candidates',
)

RELEASE_ACTIONS = (
    'push-to-releases',
)

# XXX this is a fairly clunky way of specifying which files to copy from
# candidates to releases -- let's find a nicer way of doing this.
# XXX if we keep this, let's make it configurable? overridable in config?
# Faster to update a config file in puppet than to ship a new beetmover release
# and update in puppet
RELEASE_EXCLUDE = (
    r"^.*tests.*$",
    r"^.*crashreporter.*$",
    r"^(?!.*jsshell-).*\.zip(\.asc)?$",
    r"^.*\.log$",
    r"^.*\.txt$",
    r"^.*/partner-repacks.*$",
    r"^.*.checksums(\.asc)?$",
    r"^.*/logs/.*$",
    r"^.*json$",
    r"^.*/host.*$",
    r"^.*/mar-tools/.*$",
    r"^.*robocop.apk$",
    r"^.*bouncer.apk$",
    r"^.*contrib.*",
    r"^.*/beetmover-checksums/.*$",
)

CACHE_CONTROL_MAXAGE = 3600 * 4

PRODUCT_TO_PATH = {
    'mobile': 'pub/mobile/',
    'fennec': 'pub/mobile/',
    'devedition': 'pub/devedition/',
    'firefox': 'pub/firefox/',
}
