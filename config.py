import hashlib
import os
import typing

try:
    import ujson as json
except ImportError:
    import json

import attr


CFG_LOC = os.path.split(os.path.abspath(__file__))[0]


class Config(object):
    # Hashing Function
    HMAC = 'sha512'
    # Minimum Iterations to run HMAC
    IT_MIN = 1_000_000
    # Default Number of words in the generated passphrase
    LENGTH = 4
    # Available Domains
    DOMAINS = sorted(
        [
            'google',
            'amazon',
            'neu',
            'twitter',
            'facebook',
            'eversync',
            'silabs',
            'github',
            'wellsfargo',
            'misc',
            'mlbtv',
        ]
    )
    # Raw list of words
    WORDLIST_FILE_NAME = 'wordlist.txt.gz'
    # Default shortest word length
    WLEN_MIN = 6
    # Default longest word length
    WLEN_MAX = 10
    # Salt to add to passphrase
    SALT = open('salt.txt', 'rb').read()
    # Version text
    VER = ' - '.join(
        (
            'Hash Function: {0}'.format(HMAC),
            'Min. Iterations: {0:,}'.format(IT_MIN),
            'Salt Length: {0}'.format(len(SALT)),
        )
    )


def _gt_zero_validator(instance, attribute, value):
    if value < 1:
        raise ValueError('"{0}" must be greater than 0'.format(attribute.name))


@attr.s(slots=True, auto_attribs=True)
class DomainSettings(object):
    wlen_min: int = attr.ib(
        default=Config.WLEN_MIN,
        validator=[attr.validators.instance_of(int), _gt_zero_validator],
    )
    wlen_max: int = attr.ib(
        default=Config.WLEN_MAX,
        validator=[attr.validators.instance_of(int), _gt_zero_validator],
    )
    n: int = attr.ib(default=1, validator=attr.validators.instance_of(int))
    length: int = attr.ib(
        default=Config.LENGTH,
        validator=[attr.validators.instance_of(int), _gt_zero_validator],
    )
    hmac: str = attr.ib(
        default=Config.HMAC,
        validator=[
            attr.validators.instance_of(str),
            attr.validators.in_(hashlib.algorithms_available),
        ],
    )

    def __attrs_post_init__(self):
        if self.wlen_min > self.wlen_max:
            raise ValueError(
                'wlen_min must be greater than or equal to wlen_max'
            )


@attr.s(slots=True, auto_attribs=True)
class SavedSettings(object):
    file: str = attr.ib(default='settings.json')
    settings: typing.Dict[str, DomainSettings] = attr.ib()

    @settings.default
    def settings_def(self):
        settings = dict()
        if not os.path.isfile(self.file):
            for dom in Config.DOMAINS:
                settings[dom] = DomainSettings()
        else:
            with open(self.file) as f:
                cts = json.load(f)
            for key, value in cts.items():
                settings[key] = DomainSettings(**value)
        return settings

    def save(self):
        with open(self.file, 'wt') as f:
            json.dump({k: attr.asdict(v) for k, v in self.settings.items()}, f)
        return os.path.getsize(self.file)
