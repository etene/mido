"""
MIDI messages

New messages are created with mido.new() or mido.Message(),
which both return a message object.

MIDI messages are binary encoded as one status byte followed by zero
or more data bytes. The number and meaning of the data bytes is
specific to each message type. (The exception is System Exclusive
messages which have a start byte 0xf0 and end byte 0xf7 with any
number of data bytes inbetween.)

Data bytes are 7 bit, which means their values are in range 0 -
127. The high bit is set in status bytes to signal a new message.

A table of all standard MIDI messages and their binary encoding can be
found here:

   http://www.midi.org/techspecs/midimessages.php
"""

# Pitchwheel is a 14 bit signed integer
MIN_PITCHWHEEL = -8192
MAX_PITCHWHEEL = 8191

# Song pos is a 14 bit unsigned integer
MIN_SONGPOS = 0
MAX_SONGPOS = 16383

class MessageSpec(object):
    """
    Specifications for creating a message.
    
    status_byte is the first byte of the message. For channel
    messages, the channel (lower 4 bits) is clear.

    type is the type name of the message, for example 'sysex'.

    arguments is the attributes / keywords arguments specific to
    this message type.

    size is the size of this message in bytes. This value is not used
    for sysex messages, since they use an end byte instead.
    """    

    def __init__(self, status_byte, type_, arguments, size):
        """Create a new message specification.
        """
        self.status_byte = status_byte
        self.type = type_
        self.arguments = arguments
        self.size = size
   
        # Attributes that can be set on the object
        self.valid_attributes = set(self.arguments) | {'time'}
 
    def signature(self):
        """Return call signature for Message constructor for this type.

        The signature is returned as a string.
        """
        parts = []
        parts.append(repr(self.type))

        for name in self.arguments:
            if name == 'data':
                parts.append('data=()')
            else:
                parts.append('{}=0'.format(name))
        parts.append('time=0')

        sig = '({})'.format(', '.join(parts))

        return sig

def get_message_specs():
    return [
        # Channel messages
        MessageSpec(0x80, 'note_off', ('channel', 'note', 'velocity'), 3),
        MessageSpec(0x90, 'note_on', ('channel', 'note', 'velocity'), 3),
        MessageSpec(0xa0, 'polytouch', ('channel', 'note', 'value'), 3),
        MessageSpec(0xb0, 'control_change',
                    ('channel', 'control', 'value'), 3),
        MessageSpec(0xc0, 'program_change', ('channel', 'program',), 3),
        MessageSpec(0xd0, 'aftertouch', ('channel', 'value',), 3),
        MessageSpec(0xe0, 'pitchwheel', ('channel', 'pitch',), 3),

        # System common messages
        MessageSpec(0xf0, 'sysex', ('data',), float('inf')),
        MessageSpec(0xf1, 'undefined_f1', (), 1),
        MessageSpec(0xf2, 'songpos', ('pos',), 3),
        MessageSpec(0xf3, 'song', ('song',), 2),
        MessageSpec(0xf4, 'undefined_f4', (), 1),
        MessageSpec(0xf5, 'undefined_f5', (), 1),
        MessageSpec(0xf6, 'tune_request', (), 1),
        MessageSpec(0xf7, 'sysex_end', (), 1),

        # System realtime messages
        MessageSpec(0xf8, 'clock', (), 1),
        MessageSpec(0xf9, 'undefined_f9', (), 1),
        MessageSpec(0xfa, 'start', (), 1),
        MessageSpec(0xfb, 'continue', (), 1),
        MessageSpec(0xfc, 'stop', (), 1),
        MessageSpec(0xfd, 'undefined_fd', (), 1),
        MessageSpec(0xfe, 'active_sensing', (), 1),
        MessageSpec(0xff, 'reset', (), 1),
    ]


def check_time(time):
    """Check type and value of time.
    
    Raises TypeError if value is not an integer or a float"""
    if not (isinstance(time, int) or isinstance(time, float)):
        raise TypeError('time must be an integer or float')


def check_channel(channel):
    """Check type and value of channel.

    Raises TypeError if the value is not an integer, and ValueError if
    it is outside range 0 .. 127.
    """
    if not isinstance(channel, int):
        raise TypeError('channel must be an integer')
    elif not 0 <= channel <= 15:
        raise ValueError('channel must be in range 0 .. 15')


def check_pos(pos):
    """Check type and value of song position.

    Raise TypeError if the value is not an integer, and ValueError if
    it is outside range MIN_SONGPOS .. MAX_SONGPOS.
    """
    if not isinstance(pos, int):
        raise TypeError('song pos must be and integer')
    elif not MIN_SONGPOS <= pos <= MAX_SONGPOS:
        raise ValueError('song pos must be in range {} .. {}'.format(
                MIN_SONGPOS, MAX_SONGPOS))


def check_pitch(pitch):
    """Raise TypeError if the value is not an integer, and ValueError
    if it is outside range MIN_PITCHWHEEL .. MAX_PITCHWHEEL.
    """
    if not isinstance(pitch, int):
        raise TypeError('pichwheel value must be an integer')
    elif not MIN_PITCHWHEEL <= pitch <= MAX_PITCHWHEEL:
        raise ValueError('pitchwheel value must be in range {} .. {}'.format(
                MIN_PITCHWHEEL, MAX_PITCHWHEEL))


def check_data(data_bytes):
    """Check type of data_byte and type and range of each data byte.

    Returns the data bytes as a tuple of integers.

    Raises TypeError if value is not iterable.
    Raises TypeError if one of the bytes is not an integer.
    Raises ValueError if one of the bytes is out of range 0 .. 127.
    """
    # Make the sequence immutable.
    data_bytes = tuple(data_bytes)

    for byte in data_bytes:
        check_databyte(byte)

    return data_bytes


def check_databyte(value):
    """Raise exception of byte has wrong type or is out of range

    Raises TypeError if the byte is not an integer, and ValueError if
    it is out of range. Data bytes are 7 bit, so the valid range is
    0 .. 127.
    """
    if not isinstance(value, int):
        raise TypeError('data byte must be an integer')
    elif not 0 <= value <= 127:
        raise ValueError('data byte must be in range 0 .. 127')


def encode_channel(channel):
    """Convert channel into a list of bytes. Return an empty list of
    bytes, since channel is already masked into status byte.
    """
    return ()


def encode_data(data):
    """Encode sysex data as a list of bytes. A sysex end byte (0xf7)
    is appended.
    """
    return list(data) + [0xf7]

 
def encode_pitch(pitch):
    """Encode pitchwheel pitch as a list of bytes.
    """
    pitch -= MIN_PITCHWHEEL
    return [pitch & 0x7f, pitch >> 7]


def encode_pos(pos):
    """Encode song position as a list of bytes."""
    return [pos & 0x7f, pos >> 7]


class Message(object):
    """
    MIDI message class.
    """

    # Quick lookup of specs by name or status_byte.
    _spec_lookup = {}

    # Build _spec_lookup
    for spec in get_message_specs():
        if spec.status_byte < 0xf0:
            # Channel message.
            # The upper 4 bits are message type, and
            # the lower 4 are MIDI channel.
            # We need lookup for all 16 MIDI channels.
            for channel in range(16):
                _spec_lookup[spec.status_byte | channel] = spec
        else:
            _spec_lookup[spec.status_byte] = spec

        _spec_lookup[spec.type] = spec

    del spec, channel


    def __init__(self, type_, **arguments):
        """Create a new message.

        The first argument is typically the type of message to create,
        for example 'note_on'.

        It can also be the status_byte, that is the first byte of the
        message. For channel messages, the channel (lower 4 bits of
        the status_byte) is masked out from the lower 4 bits of the
        status byte. This can be overriden by passing the 'channel'
        keyword argument.
        """
        try:
            spec = self._spec_lookup[type_]
        except KeyError:
            text = '{!r} is an invalid type name or status byte'
            raise ValueError(text.format(type_))

        self._set('_spec', spec)
        self._set('type', self._spec.type)

        #
        # Set default values for attributes
        #
        for name in self._spec.arguments:
            if name == 'data':
                self.data = ()
            elif name == 'channel':
                # This is a channel message, so if the first
                # argument to this function was a status_byte,
                # the lower 4 bits will contain the channel.
                if isinstance(type_, int):
                    self.channel = type_ & 0x0f
                else:
                    self.channel = 0
            else:
                setattr(self, name, 0)
        self._set('time', 0)

        #
        # Override attibutes with keyword arguments
        #
        for name, value in arguments.items():
            try:
                setattr(self, name, value)
            except AttributeError:
                raise ValueError('{!r} is an invalid ' \
                                     'keyword argument for this message type' \
                                     ''.format(name))

    def copy(self, **overrides):
        """Return a copy of the message.

        Attributes will be overriden by the passed keyword arguments.
        Only message specific attributes can be overriden. The message
        type can not be changed.

        Example:

            a = Message('note_on')
            b = a.copy(velocity=32)
        """
        # Get values from this object
        arguments = {}
        for name in self._spec.arguments + ('time',):
            if name in overrides:
                arguments[name] = overrides[name]
            else:
                arguments[name] = getattr(self, name)

        return Message(self.type, **arguments)

    def _set(self, name, value):
        """Sets an attribute directly, bypassing all type and value checks"""
        self.__dict__[name] = value

    def __setattr__(self, name, value):
        """Set an attribute."""

        if name in self._spec.valid_attributes:
            try:
                check = globals()['check_{}'.format(name)]
            except KeyError:
                check = check_databyte

            ret = check(value)
            if name == 'data':
                value = ret

            self.__dict__[name] = value
        elif name in self.__dict__:
            raise AttributeError('{} attribute is read only'.format(name))
        else:
            raise AttributeError('{} message has no attribute {}'.format(
                    self.type, name))

    def __delattr__(self, name):
        raise AttributeError('attribute can not be deleted')

    def _get_status_byte(self):
        """Compute and return status byte.

        For channel messages, the returned status byte
        will contain the channel in its lower 4 bits.
        """
        byte = self._spec.status_byte
        if byte < 0xf0:
            # Add channel (lower 4 bits) to status byte.
            # Those bits in spec.status_byte are always 0.
            byte |= self.channel
        return byte

    status_byte = property(fget=_get_status_byte)
    del _get_status_byte

    def bytes(self):
        """Encode message and return as a list of integers."""
        message_bytes = [self.status_byte]

        for name in self._spec.arguments:
            value = getattr(self, name)
            try:
                encode = globals()['encode_{}'.format(name)]
                message_bytes.extend(encode(value))
            except KeyError:
                message_bytes.append(value)

        return message_bytes

    def bytearray(self):
        """Encode message and return as a bytearray.

        This can be used to write the message to a file.
        """
        return bytearray(self.bytes())

    def hex(self, sep=' '):
        """Encode message and return as a string of hex numbers,

        Each number is separated by the string sep.
        """
        return sep.join(['{:02X}'.format(byte) for byte in self.bytes()])

    def __repr__(self):
        parts = [self.type]

        for name in self._spec.arguments + ('time',):
            parts.append('{}={!r}'.format(name, getattr(self, name)))

        return 'mido.Message({})'.format(', '.join(parts))

    def __str__(self):
        return text_format(self)

    def __eq__(self, other):
        """Compare message to another for equality.
        
        Key for comparison: (msg.type, msg.channel, msg.note, msg.velocity).
        """
        if not isinstance(other, Message):
            raise TypeError('comparison between Message and another type')

        def key(msg):
            """Return a key for comparison."""
            return [msg.type] + [getattr(msg, arg) for arg in msg._spec.arguments]

        return key(self) == key(other)


def text_parse_number(text):
    """Parse text as a number.

    Return number or None if text is not a number."""

    for convert in [int, float]:
        try:
            return convert(text)
        except ValueError:
            continue
    else:
        return None

def text_parse(text):
    """Parse a string of text and return a message.

    The string can span multiple lines, but must contain
    one full message.

    Raises ValueError if the string could not be parsed.
    """
    words = text.split()
    if len(words) < 1:
        raise ValueError('string is empty')

    time = text_parse_number(words[0])
    if time is not None:
        del words[0]
        if len(words) < 1:
            raise ValueError('no message found after number')

    message = Message(words[0])
    if time:
        message.time = time

    arguments = words[1:]
    valid_arguments = message._spec.arguments

    names_seen = set()

    for argument in arguments:
        try:
            name, value = argument.split('=')
        except ValueError:
            raise ValueError('missing or extraneous equals sign')

        if name in names_seen:
            raise ValueError('argument passed more than once')
        names_seen.add(name)

        if name == 'data':
            if not value.startswith('(') and value.endswith(')'):
                raise ValueError('missing parentheses in data message')

            try:
                data_bytes = [int(byte) for byte in value[1:-1].split(',')]
            except ValueError:
                raise ValueError('unable to parse data bytes')
            setattr(message, 'data', data_bytes)
        else:
            try:
                setattr(message, name, int(value))
            except AttributeError as exception:
                raise ValueError(exception.message)

    return message


def text_parse_stream(stream):
    """Parse a stram of messages and yield (message, error_message)

    stream can be any iterable that generates text strings. If
    a line can be parsed, (message, None) is returned. If it can't
    be parsed (None, error_message) is returned. The error message
    containes the line number where the error occured.
    """
    line_number = 1
    for line in stream:
        try:
            line = line.split('#')[0].strip()
            if line:
                yield parse(line), None
        except ValueError as exception:
            error_message = 'line {line_number}: {message}'.format(
                line_number=line_number,
                message=exception.message)
            yield None, error_message            
        line_number += 1


def text_format(message, include_time=False):
    """Format a message and return as a string."""
    if not isinstance(message, Message):
        raise ValueError('message must be a mido.Message object')

    words = []
    if include_time:
        words.append(str(message.time))
    words.append(message.type)
    for name in message._spec.arguments:
        value = getattr(message, name)
        if name == 'data':
            value = '({})'.format(','.join([str(byte) for byte in value]))
        words.append('{}={}'.format(name, value))
    
    return ' '.join(words)