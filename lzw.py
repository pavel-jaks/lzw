from argparse import ArgumentParser
from collections.abc import Sized
from enum import Enum
from os import path
from typing import Union, BinaryIO, List, SupportsInt


class ProcedureType(Enum):
    """
    Enum to denote what to do in the main program
    """
    COMPRESS = 0
    DECOMPRESS = 1


class ConstantCodes(Enum):
    """
    Enum to denote special codes
    """
    CLEAR_DICTIONARY = 256
    END_OF_DATA = 257


class Bits(Sized, SupportsInt):
    """
    Class to represent bits
    """

    def __init__(self, number: Union[int, List[bool]]):
        """
        Constructor of Bits class
        :param number: if int then denotes the value of bits property else it's bits backwards
        """
        if type(number) is list:
            self.bits = [number[-index] for index in range(1, len(number) + 1)]
        else:
            bits = []
            key_str = f'{number:b}'
            key_len = len(key_str)
            for digit_index in range(1, key_len + 1):
                bits.append(key_str[-digit_index] == '1')
            self.bits = [bits[-index] for index in range(1, len(bits) + 1)]

    def __len__(self):
        """
        Override of method that is used in len() built-in function
        :return: Returns the length of the underlying bits array
        """
        return len(self.bits)

    def binary_length(self):
        """
        Method to return the length of binary number that is represented by bits property
        :return: Length of underlying number in binary
        """
        length = 0
        for i in range(1, len(self.bits) + 1):
            if self.bits[-i]:
                length = i
        return length

    def __int__(self):
        """
        Override of method called while executing int() built-in function with Bits class as a parameter
        :return: The integer value of Bits
        """
        integer = 0
        for boolean in self.bits:
            integer *= 2
            integer += 1 if boolean else 0
        return integer


class CompressionDictionary:
    """
    Class to encapsulate compression dictionary
    """

    DICT_SIZE = 12  # Max size of a code stored in dictionary

    def __init__(self):
        """
        Constructor of CompressionDictionary class
        """
        self.dict = {}
        self.last_used_code = 257

    def __getitem__(self, key: Union[bytes, ConstantCodes]) -> Bits:
        """
        Method of indexing CompressionDictionary instance like a dictionary
        :param key: Key value of which shall be retrieved
        :return: Returns the Bits value corresponding to key
        """
        if type(key) is ConstantCodes:
            return Bits(key.value)
        if len(key) == 1:
            return Bits(key[0])
        return self.dict[key]

    def next_code(self) -> int:
        """
        Increases the value of last used code and then returns it
        :return: new value of last used code
        """
        self.last_used_code += 1
        return self.last_used_code

    def add(self, new_key: bytes) -> None:
        """
        Adds new word to the dictionary generating new code
        :param new_key: Word to be stored
        :return: None
        """
        new_bits = Bits(self.next_code())
        if len(new_bits) > self.DICT_SIZE:
            raise OverflowError("Compression dictionary is full")
        self.dict[new_key] = new_bits

    def __contains__(self, item: bytes) -> bool:
        """
        Implementation of in keyword for checking whether key-item is in dictionary
        :param item: key to be checked
        :return: boolean value
        """
        if len(item) == 1:
            return True
        return item in self.dict

    def is_full(self) -> bool:
        """
        Checks whether the dictionary is full
        :return: boolean value of fullness of the dictionary
        """
        return len(Bits(self.last_used_code + 1)) > self.DICT_SIZE

    def clear(self) -> None:
        """
        Clears the dictionary
        :return: None
        """
        self.dict.clear()
        self.last_used_code = 257


class CompressionBuffer:
    """
    Buffer for writing bytes to file
    """
    def __init__(self, out_file: BinaryIO):
        """
        Constructor of CompressionBuffer class
        :param out_file: File in which bytes will be written
        """
        self.out_file = out_file
        self.not_written_bits = []

    @staticmethod
    def bits_to_bytes(bits: List[bool]) -> bytes:
        """
        Method to convert list of bits to bytes object
        :param bits: List of bits to be converted
        :return: Bytes representation of bits parameter
        """
        if len(bits) % 8 != 0:
            raise ValueError()
        integer = 0
        for i in range(len(bits)):
            integer *= 2
            if bits[i]:
                integer += 1
        return integer.to_bytes(1, 'big', signed=False)

    def append(self, bits: Bits) -> None:
        """
        Method to append Bits object to file
        :param bits: Bits object to be appended to the file
        :return: None
        """
        for bit in bits.bits:
            self.not_written_bits.append(bit)
            if len(self.not_written_bits) == 8:
                self.out_file.write(self.bits_to_bytes(self.not_written_bits))
                self.not_written_bits.clear()

    def flush(self) -> None:
        """
        Method to flush not written bits to the file and finish writing by adding necessary bits to complete byte
        :return: None
        """
        if len(self.not_written_bits) == 0:
            return
        self.append(Bits([False for _ in range(8 - len(self.not_written_bits))]))


class ReaderBuffer:
    """
    Class created as an attempt to accelerate the program by buffering the input file; not much success
    """
    def __init__(self, in_file: BinaryIO, buffer_size: int = 1024 * 1024):
        """
        Constructor of ReaderBuffer
        :param in_file: File to be read
        :param buffer_size: Size of a buffer (in bytes)
        """
        self.in_file = in_file
        self.current_index = 0
        self.buffer_size = buffer_size
        self.current_bytes = self.in_file.read(self.buffer_size)

    def next_bytes(self) -> Union[bytes, None]:
        """
        Method to return nex byte of the file as a bytes object
        :return: Next bytes
        """
        if self.current_index == len(self.current_bytes) and self.current_index < self.buffer_size:
            return None
        foo = self.current_bytes[self.current_index]
        if self.current_index == self.buffer_size - 1:
            self.current_index = 0
            self.current_bytes = self.in_file.read(self.buffer_size)
        else:
            self.current_index += 1
        return foo.to_bytes(1, byteorder='big', signed=False)


class CompressionEngine:
    """
    Compression engine class
    """

    def __init__(self):
        """
        Constructor of CompressionEngine class
        """
        self.dict = CompressionDictionary()

    @staticmethod
    def pad(bits: Bits, length: int) -> Bits:
        """
        Method to give given Bits object given length
        :param bits: Bits object to be padded by adding extra False bits to the beginning
        :param length: Length of returned Bits object
        :return: Bits object padded to given length
        """
        new_bits = Bits([False for _ in range(length)])
        for i in range(1, len(bits) + 1):
            foo = bits.bits[len(bits) - i]
            new_bits.bits[length - i] = foo
        return new_bits

    def compress(self, in_file: BinaryIO, out_file: BinaryIO) -> None:
        """
        Implementation of Lempel-Ziv-Welch 84 compression algorithm
        :param in_file: File to be compressed
        :param out_file: File to be written the compressed data in
        :return: None
        """
        in_buffer = ReaderBuffer(in_file)
        out_buffer = CompressionBuffer(out_file)

        current_byte = in_buffer.next_bytes()
        current_padding = 9

        current_word = current_byte
        current_byte = in_buffer.next_bytes()

        while current_byte:
            word = current_word + current_byte
            if word in self.dict:
                current_word = word
                current_byte = in_buffer.next_bytes()
                continue
            if self.dict.is_full():
                out_buffer.append(self.pad(self.dict[current_word], current_padding))
                out_buffer.append(self.pad(self.dict[ConstantCodes.CLEAR_DICTIONARY], current_padding + 1))
                self.dict.clear()
                current_padding = 9
            else:
                out_buffer.append(self.pad(self.dict[current_word], current_padding))
                self.dict.add(word)
                if self.dict[word].binary_length() > current_padding:
                    current_padding += 1
                # out_buffer.append(self.pad(self.dict[current_word], current_padding))

            current_word = current_byte
            current_byte = in_buffer.next_bytes()
        out_buffer.append(self.pad(self.dict[current_word], current_padding))

        out_buffer.append(self.pad(self.dict[ConstantCodes.END_OF_DATA], current_padding))
        out_buffer.flush()


class DecompressionReaderBuffer:
    """
    Class to encapsulate work with the in file for decompression
    """

    def __init__(self, in_file: BinaryIO):
        """
        Constructor of DecompressionReaderBuffer
        :param in_file: File to be read
        """
        self.in_file = in_file
        self.not_yielded_bits = []

    def add_bytes(self, next_bytes: bytes) -> None:
        """
        Method to add bytes as bits to not_yielded_bits list
        :param next_bytes: Bytes to be added
        :return: None
        """
        for byte in next_bytes:
            bits = Bits(byte).bits
            for _ in range(8 - len(bits)):
                self.not_yielded_bits.append(False)
            for boo in bits:
                self.not_yielded_bits.append(boo)

    def next_bits(self, bits_count: int) -> Union[Bits, None]:
        """
        Method to yield next n bits of in file
        :param bits_count: Number of bits to be yielded
        :return: Bits object representing the bits in the in file
        """
        bits = Bits([False for _ in range(bits_count)])
        while bits_count > len(self.not_yielded_bits):
            foo = self.in_file.read(1)
            if len(foo) == 0:
                break
            self.add_bytes(foo)
        for i in range(min([bits_count, len(self.not_yielded_bits)])):
            bits.bits[i] = self.not_yielded_bits[0]
            self.not_yielded_bits.pop(0)
        return bits


class DecompressionDictionary:
    """
    Class to represent decompression dictionary
    """

    def __init__(self):
        """
        Constructor of DecompressionDictionary
        """
        self.dict = [i.to_bytes(1, byteorder='big', signed=False) for i in range(256)]
        self.dict.append(b'0')
        self.dict.append(b'0')
        self.last_used_index = 257

    def __getitem__(self, key: Bits) -> bytes:
        """
        Method to override indexing of the class as of a dictionary
        :param key: Code of bits whose corresponding word will be retrieved
        :return: The word represented by key code
        """
        return self.dict[int(key)]

    def __contains__(self, item: Bits) -> bool:
        """
        Method that overrides the usage of in keyword - to check whether given code is in dictionary
        :param item: Bits representing the code to be checked
        :return: Boolean value of the check
        """
        return int(item) <= self.last_used_index

    def clear(self) -> None:
        """
        Method that clears the dictionary
        :return: None
        """
        self.last_used_index = 257

    def add(self, value: bytes) -> None:
        """
        Method that adds given bytes value to the dictionary while generating its code
        :param value: Word to be added to the dictionary
        :return: None
        """
        self.last_used_index += 1
        if self.last_used_index == len(self.dict):
            self.dict.append(value)
        else:
            self.dict[self.last_used_index] = value

    def len_of_last(self) -> int:
        """
        Method to retrieve information about the length of last used code in binary
        :return: Integer that represents the length of the last code in binary
        """
        return len(f'{self.last_used_index:b}')

    def is_full_in_order(self) -> bool:
        """
        Method that checks whether the dictionary is full in order i.e. the next code will be represented by longer bits
        :return: Boolean value of the result of the check
        """
        return not f'{self.last_used_index:b}'.__contains__('0')


class DecompressionEngine:
    """
    Decompression engine class
    """

    def __init__(self):
        """
        Constructor of DecompressionEngine class
        """
        self.dict = DecompressionDictionary()

    def decompress(self, in_file: BinaryIO, out_file: BinaryIO) -> None:
        """
        Implementation of Lempel-Ziv-Welch 84 decompression algorithm
        :param in_file: File to be decompressed
        :param out_file: File in which the decompressed data will be written
        :return: None
        """
        in_buffer = DecompressionReaderBuffer(in_file)
        current_padding = 9
        current_bits = in_buffer.next_bits(current_padding)
        current_word = self.dict[current_bits]
        last_word = current_word
        current_bits = in_buffer.next_bits(current_padding)
        while int(current_bits) != ConstantCodes.END_OF_DATA.value:
            out_file.write(last_word)
            if int(current_bits) == ConstantCodes.CLEAR_DICTIONARY.value:
                self.dict.clear()
                current_padding = 9
                current_bits = in_buffer.next_bits(current_padding)
                last_word = self.dict[current_bits]
                current_bits = in_buffer.next_bits(current_padding)
                continue

            if current_bits not in self.dict:
                current_word = last_word + last_word[0].to_bytes(1, byteorder='big', signed=False)
                self.dict.add(current_word)
            else:
                current_word = self.dict[current_bits]
                self.dict.add(last_word + current_word[0].to_bytes(1, byteorder='big', signed=False))

            last_word = current_word
            if self.dict.is_full_in_order():
                current_padding += 1
            current_bits = in_buffer.next_bits(current_padding)

        out_file.write(last_word)


def main(procedure_type: ProcedureType, in_file: str, out_file: Union[str, None]) -> None:
    """
    Main function of the lzw program
    :param procedure_type: Type of procedure to be conducted - decompression or compression
    :param in_file: File to be processed
    :param out_file: File to be written in the product of the program process
    :return: None
    """
    if procedure_type == ProcedureType.COMPRESS:
        try:
            with open(in_file, mode='rb') as in_stream:
                if out_file is None:
                    out_file = '.'.join([path.splitext(in_file)[0], 'lzw'])
                with open(out_file, mode='wb') as out_stream:
                    CompressionEngine().compress(in_stream, out_stream)
        except FileNotFoundError:
            print('Given file does not exist')
    else:
        try:
            with open(in_file, mode='rb') as in_stream:
                if out_file is None:
                    out_file = '.'.join([path.splitext(in_file)[0], 'txt'])
                with open(out_file, mode='wb') as out_stream:
                    DecompressionEngine().decompress(in_stream, out_stream)
        except FileNotFoundError:
            print('Given file does not exist')


if __name__ == "__main__":
    parser = ArgumentParser(
        description='Program to apply LZW compression or decompression algorithm on given file'
    )
    parser.add_argument(
        'in_file',
        help='File to be processed'
    )
    parser.add_argument(
        '-d',
        action='store_const',
        dest='decompress',
        const=True,
        default=False,
        help='Flag to denote that the program should decompress the given file'
    )
    parser.add_argument(
        '--out_file',
        default=None,
        type=str,
        help='Destination file of the process; if not specified,'
             'path given as in_file will be used with changed extension'
    )
    args = parser.parse_args()
    main(
        procedure_type=ProcedureType.DECOMPRESS if args.decompress else ProcedureType.COMPRESS,
        in_file=args.in_file,
        out_file=args.out_file
    )
