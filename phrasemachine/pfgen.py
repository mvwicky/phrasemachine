import base64
import gzip
import hashlib
import random
import re
from typing import Text, Pattern, List, ByteString


def get_words(file_name: Text, reg: Pattern) -> List[Text]:
    """Load words from a wordlist file

    file_name: the name (path) of the file from which we'll load words
    reg: a compiled regular expression object to match against
    """
    with open(file_name, 'rb') as f:
        cts = gzip.decompress(f.read()).decode()
    words: List[Text] = []
    for elem in reg.finditer(cts):
        words.append(elem[0].title())
    return words


def word_reg(wmin: int, wmax: int) -> Pattern:
    """Generates a compiled regular expression that matches words in the
    wordlist file

    wmin: the minimum word length
    wmax: the maximum word length
    """
    wmin, wmax = str(wmin), str(wmax)
    return re.compile(r'^[a-z]{' + wmin + ',' + wmax + '}$', re.MULTILINE)


def generate_key(
    master: Text,
    domain: Text,
    hmac: Text,
    it_min: int,
    num: int,
    salt: ByteString,
) -> Text:
    """Generate a key which will be used as a seed to an RNG

    master: the master password
    domain: the domain which we're generating passwords for
    num: the number of iterations (past max) to run
    """
    master_hash = hashlib.new(hmac, master.encode()).hexdigest()
    md_bytes = (master_hash + '/' + domain).encode('utf-8')

    def pf_bytes(domain, it_min, num):
        return hashlib.pbkdf2_hmac(hmac, md_bytes, salt, it_min + num)

    return base64.b64encode(pf_bytes(domain, it_min, num)).decode()


def generate_passphrase(
    master: Text,
    domain: Text,
    hmac: Text,
    it_min: int,
    num: int,
    words: List[Text],
    length: int,
    salt: ByteString,
) -> Text:
    """Actually generate the password

    master: the master password
    domain: the site/service for which we're creating a passphrase
    hmac: the name of a hash function
    it_min: minumum iterations
    num: the iteration we're on
    words: the actual word list
    length: the number of words to use (from command line)
    """

    # Generate key in base64
    key = generate_key(master, domain, hmac, it_min, num, salt)
    # Seed the RNG with the generated key
    random.seed(key)
    # Generate a passphrase
    return ''.join(random.choices(words, k=length))


if __name__ == '__main__':
    print(dir(generate_passphrase))
    print(generate_passphrase.__annotations__)
