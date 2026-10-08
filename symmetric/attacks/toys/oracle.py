from minifeistel import miniFeistel
from optimized_minispn import miniSPN
import os
import secrets
import sqlite3
import time

FLAG_SPN     = os.getenv('FLAG_SPN'    , 'kitsu{this_just_is_a_test_flag_for_spn}'    )
FLAG_FEISTEL = os.getenv('FLAG_FEISTEL', 'kitsu{this_just_is_a_test_flag_for_feistel}')

DB_PATH    = os.getenv('DB_PATH', 'sessions.db')
BLOCK_BITS = 48
SESSION_TTL = 3600

CIPHERS = {'1': miniSPN, '2': miniFeistel}

cipher_chosen_menu = '''Choose cipher for oracle:
  1. MiniSPN
  2. MiniFeistel
>>> '''

option_chosen_menu = '''Choose action you want:
  1. Encrypt
  2. Decrypt
  3. Check key
  4. Exit
>>> '''

session_menu = 'Session ID (press Enter to create a new one)\n>>> '


def db_init():
    con = sqlite3.connect(DB_PATH, timeout=10)
    try:
        con.execute('PRAGMA journal_mode=WAL')
    except sqlite3.DatabaseError:
        pass
    con.execute('''CREATE TABLE IF NOT EXISTS sessions (
        sid     TEXT PRIMARY KEY,
        cipher  TEXT NOT NULL,
        key     BLOB NOT NULL,
        created REAL NOT NULL
    )''')
    con.execute('DELETE FROM sessions WHERE created < ?', (time.time() - SESSION_TTL,))
    con.commit()
    return con

def new_session(con, cid):
    sid = secrets.token_hex(8)
    key = os.urandom(6)
    con.execute('INSERT INTO sessions (sid, cipher, key, created) VALUES (?, ?, ?, ?)',
                (sid, cid, key, time.time()))
    con.commit()
    return sid, key

def load_session(con, sid, cid):
    row = con.execute('SELECT key FROM sessions WHERE sid = ? AND cipher = ?',
                      (sid, cid)).fetchone()
    return row[0] if row else None


def choose_cipher():
    cid = input(cipher_chosen_menu).strip()
    if cid in CIPHERS:
        return cid
    print('Invalid choice!')

def byte2bit(bs):
    return [(b >> i) & 1 for b in bs for i in range(7, -1, -1)]

def bit2hex(bits):
    return ''.join(
        '%x' % (bits[i] << 3 | bits[i+1] << 2 | bits[i+2] << 1 | bits[i+3])
        for i in range(0, len(bits), 4)
    )

def input_hex(prompt):
    while True:
        h = input(prompt).strip()
        if not h or len(h) % 12 != 0:
            print('Length of hex must be a non-zero multiple of 12')
            continue
        try:
            return byte2bit(bytes.fromhex(h))
        except ValueError:
            print('Invalid hex!')
            continue

def run(fn, bits):
    out = []
    for i in range(0, len(bits), BLOCK_BITS):
        out.extend(fn(bits[i:i+BLOCK_BITS]))
    return out


def main():
    while (cid := choose_cipher()) is None:
        pass
    cipher = CIPHERS[cid]

    con = db_init()
    key_bytes = None
    while key_bytes is None:
        sid = input(session_menu).strip()
        if not sid:
            sid, key_bytes = new_session(con, cid)
            print('Your session ID:', sid)
        else:
            key_bytes = load_session(con, sid, cid)
            if key_bytes is None:
                print('Session not found!')
    con.close()

    key = byte2bit(key_bytes)
    cipher.add_key(key)

    while True:
        match input(option_chosen_menu).strip():
            case '1':
                plt = input_hex('Enter plaintext\n>>> ')
                print('Your encrypted:', bit2hex(run(cipher.encrypt_block, plt)))
            case '2':
                cpt = input_hex('Enter ciphertext\n>>> ')
                print('Your decrypted:', bit2hex(run(cipher.decrypt_block, cpt)))
            case '3':
                if key == input_hex('Enter your key\n>>> '):
                    print('CONGRATULATION!!! -> FLAG:', FLAG_SPN if cid == '1' else FLAG_FEISTEL)
                    exit(0)
                else:
                    print('WRONG KEY!!!')
            case '4':
                exit(0)
            case _:
                print('Invalid choice!')


if __name__ == '__main__':
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        pass