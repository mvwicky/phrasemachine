"""Generates random passphrases based on a wordlist

TODO: look into making the salt an environment variable or something like that
TODO: check the master password against a saved hash
"""

import argparse
import base64
import hashlib
import getpass
import gzip
import random
import re

import click
import pyperclip

from config import Config, SavedSettings, DomainSettings


def word_reg(wmin, wmax):
    """Generates a compiled regular expression that matches words in the
    wordlist file

    wmin: the minimum word length
    wmax: the maximum word length
    """
    wmin, wmax = str(wmin), str(wmax)
    return re.compile(r'^[a-z]{' + wmin + ',' + wmax + '}$', re.MULTILINE)


def create_parser():
    """Checks command line arguments, returns argparse namespace object"""
    # The main argument parser object
    parser = argparse.ArgumentParser(prog='passphrase')
    parser.add_argument(
        'domain',
        type=str,
        choices=Config.DOMAINS,
        metavar='DOMAIN',
        help='the domain for which a passphrase is generated ({0})'.format(
            ', '.join(Config.DOMAINS)
        ),
    )
    parser.add_argument(
        '--num',
        '-n',
        type=int,
        default=1,
        help='passphrase number to generate (default {0})'.format(1),
    )
    parser.add_argument(
        '--length',
        '-l',
        type=int,
        default=Config.LENGTH,
        help='number of words in the passphrase (default: {0})'.format(
            Config.LENGTH
        ),
    )
    parser.add_argument(
        '--length-min',
        type=int,
        default=Config.WLEN_MIN,
        help='the minumum length of a word (default: {0})'.format(
            Config.WLEN_MIN
        ),
    )
    parser.add_argument(
        '--length-max',
        type=int,
        default=Config.WLEN_MAX,
        help='the maximum length of a word (default: {0})'.format(
            Config.WLEN_MAX
        ),
    )
    parser.add_argument(
        '--hmac',
        type=str,
        default=Config.HMAC,
        choices=hashlib.algorithms_available,
        metavar='HMAC',
        help='the hash function to use with PBKDF2 (default: {0})'.format(
            Config.HMAC
        ),
    )
    parser.add_argument(
        '--it-min',
        type=int,
        default=Config.IT_MIN,
        help='the minimum iterations for PBKDF2 (default: {0})'.format(
            Config.IT_MIN
        ),
    )
    parser.add_argument(
        '--version', '-v', action='version', version=Config.VER
    )
    return parser


@click.command()
@click.argument(
    'domain',
    type=click.Choice(Config.DOMAINS),
    help='for domain for which a passphrase is generated')
@click.option(
    '--num', '-n', type=int, default=1, help='passphrase number to generate'
)
@click.option(
    '--length',
    '-l',
    type=int,
    default=Config.LENGTH,
    help='number of words in the passphrase'
)
@click.option(
    '--wlen_min',
    type=int,
    default=Config.WLEN_MIN,
    help='the minumum length of a word'
)
@click.option(
    '--wlen_max',
    type=int,
    default=Config.WLEN_MAX,
    help='the minumum length of a word'
)
@click.option(
    '--hmac',
    type=click.Choice(hashlib.algorithms_available),
    default=Config.HMAC,
    help='the hash function to use with PBKDF2'
)
@click.option(
    '--it-min',
    type=int,
    default=Config.IT_MIN,
    help='the minimum iterations for PBKDF2'
)
@click.option('--update/--no-update', default=False)
def cli(domain, num, length, wlen_min, wlen_max, hmac, it_min, update):
    """Click main function"""
    settings = SavedSettings()
    inp_settings = DomainSettings(
        wlen_min, wlen_max, num, length, hmac, it_min
    )


def _get_ns():
    p = create_parser()
    ns = vars(p.parse_args([Config.DOMAINS[0]]))
    return list(ns.keys())


def check_args():
    parser = create_parser()
    args = parser.parse_args()
    if args.length_min > args.length_max:
        # Behavior here is undefined, may cause a regex error at some point
        raise RuntimeError('min word length > max word length')

    return args


def get_words(file_name, reg):
    """Load words from a wordlist file

    file_name: the name (path) of the file from which we'll load words
    reg: a compiled regular expression object to match against
    """
    with open(Config.WORDLIST_FILE_NAME, 'rb') as f:
        cts = gzip.decompress(f.read()).decode()
    words = []
    for elem in reg.finditer(cts):
        words.append(elem[0].title())
    return words


def generate_key(master, domain, hmac, it_min, num):
    """Generate a key which will be used as a seed to an RNG

    master: the master password
    domain: the domain which we're generating passwords for
    num: the number of iterations (past max) to run
    """
    master_hash = hashlib.new(hmac, master).hexdigest()
    md_bytes = (master_hash + '/' + domain).encode('utf-8')

    def pf_bytes(domain, it_min, num):
        return hashlib.pbkdf2_hmac(hmac, md_bytes, Config.SALT, it_min + num)

    return base64.b64encode(pf_bytes(domain, it_min, num)).decode()


def generate_passphrase(master, domain, hmac, it_min, num, words, length):
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
    key = generate_key(master, domain, hmac, it_min, num)
    # Seed the RNG with the generated key
    random.seed(key)
    # Generate a passphrase
    return ''.join(random.choices(words, k=length))


def gen(settings: DomainSettings):
    pass


def save_settings():
    pass


def main():
    """Main function

    args: an argparse namespace
    """
    # Load available words
    args = check_args()
    dom_set = DomainSettings()
    words = get_words(
        Config.WORDLIST_FILE_NAME, word_reg(args.length_min, args.length_max)
    )
    click.echo(Config.VER)
    # Get the master password from the user in a discrete way
    master = getpass.getpass(prompt='Enter Master Password: ')
    passphrase = generate_passphrase(
        master,
        args.domain,
        args.hmac,
        args.it_min,
        args.num,
        words,
        args.length
    )
    click.echo(passphrase)
    # Copy to the clipboard
    pyperclip.copy(passphrase)


if __name__ == '__main__':
    # parser = create_parser()
    main()
    # cli()
