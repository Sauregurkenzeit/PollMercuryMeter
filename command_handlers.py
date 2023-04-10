def handle_command_base(out):
    value = out[3:-2]
    return int.from_bytes(value, byteorder='big')


def handle_command_27(out):
    # ... (handle the response for command \x27)
    data = ''.join('{:02x}'.format(c) for c in out[5:9])
    result = f"{data}"
    return result


def handle_command_63(out):
    # ... (handle the response for command \x63)
    result = f"Result for command 63: ..."
    return result