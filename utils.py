_longest_message_length = 1


def clear_then_overwrite_print(message: str) -> None:
    # clearing anything left from previous prints using this function
    global _longest_message_length
    print(" " * _longest_message_length, end="\r")
    _longest_message_length = max(_longest_message_length, len(message))
    # actually printing the message
    print(message, end="\r")
