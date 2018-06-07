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
            'mlbtv'
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
