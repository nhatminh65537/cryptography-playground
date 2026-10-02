from minifeistel import miniFeistel
from minispn import miniSPN
import secrets
import os

FLAG_SPN     = os.getenv('FLAG_SPN'    , 'kitsu{this_just_is_a_test_flag_for_spn}'    )
FLAG_FEISTEL = os.getenv('FLAG_FEISTEL', 'kitsu{this_just_is_a_test_flag_for_feistel}')

cipher_chosen_menu = '''Choose cipher for oracle:
  1. MiniSPN
  2. MiniFeistel
>>> '''

def choose_cipher():
    cipher_chosen = input(cipher_chosen_menu)
    
    if cipher_chosen == '1': return miniSPN
    elif cipher_chosen == '2': return miniFeistel

    print('Invalid choice!')

option_chosen_menu = '''Choose action you want:
  1. Encrypt
  2. Decrypt
  3. Check key
  4. Exit
>>> '''

def byte2bit(b):
    return list(map(int, f'{int.from_bytes(b, 'little'):b}'.zfill(48)))

def hex2bit(h):
    return byte2bit(bytes.fromhex(h))

def input_block_hex(prompt):
    while True:
        h = input(prompt)
        try:
            block = hex2bit(h)
        except:
            print('Invalid hex!')
            continue

        if len(block) != 48:
            print('Length of block must be 48 bits')
            continue

        return block

def output_block_hex(format, block):
    i = int(''.join(map(str, block)), 2)
    print(format % f'{i:012x}')

def main():
    while (cipher := choose_cipher()) is None:
        pass

    key = byte2bit(os.urandom(6))
    cipher.add_key(key)

    while True:        
        match input(option_chosen_menu):
            case '1':
                plt = input_block_hex('Enter plaintext block\n>>> ')
                cpt = cipher.encrypt_block(plt)
                output_block_hex('Your encrypted block: %s', cpt)
            case '2':
                cpt = input_block_hex('Enter ciphertext block\n>>> ')
                plt = cipher.decrypt_block(cpt)
                output_block_hex('Your decrypted block: %s', plt)
            case '3':
                if key == input_block_hex('Enter ciphertext block\n>>> '):
                    print('CONGRATULATION!!! -> FLAG:', FLAG_SPN if cipher is miniSPN else FLAG_FEISTEL)
                else:
                    print('WRONG KEY!!!')
            case '4':
                exit(0)


if __name__ == '__main__':
    main()
    