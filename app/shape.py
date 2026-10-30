def regular_shape(array):
    """
    Return the shape of a rectangular array (list of lists ... of non-lists)
    as a tuple, e.g. (2, 3) for a 2x3 matrix. A single entry has shape ().
    Returns None if the array is irregular (ragged or mixed nesting).
    """
    if not isinstance(array, list):
        return ()
    if len(array) == 0:
        return (0,)

    shapes = [regular_shape(x) for x in array]
    if any(s is None for s in shapes) or any(s != shapes[0] for s in shapes):
        return None
    return (len(array),) + shapes[0]


def format_loc(loc):
    return "(" + ",".join(str(i) for i in loc) + ")"


def plural(n, word, word_plural=None):
    if n == 1:
        return f"{n} {word}"
    return f"{n} {word_plural or word + 's'}"


def entries(n):
    return plural(n, "entry", "entries")


def describe_shape(shape):
    if len(shape) == 1:
        return entries(shape[0])
    if len(shape) == 2:
        return f"{plural(shape[0], 'row')} and {plural(shape[1], 'column')}"
    return "size " + " x ".join(str(n) for n in shape)


def find_mismatch(response, answer, loc):
    """
    Return a message describing the first place where the response
    does not have the same nested structure as the answer, or None.
    """
    where = f"Entry {format_loc(loc)}" if loc else "Your response"

    if not isinstance(answer, list):
        if isinstance(response, list):
            return f"{where} should be a single expression, not a list."
        return None

    if not isinstance(response, list):
        return f"{where} should be a list of {entries(len(answer))}, not a single expression."

    if len(response) != len(answer):
        return f"{where} has {entries(len(response))}, but should have {entries(len(answer))}."

    for i in range(len(answer)):
        message = find_mismatch(response[i], answer[i], loc + [i + 1])
        if message is not None:
            return message

    return None


def shape_feedback(response, answer):
    """
    Return feedback explaining how the size of the response differs
    from the answer, or None if they have the same shape.
    """
    message = find_mismatch(response, answer, [])
    if message is None:
        return None

    response_shape = regular_shape(response)
    answer_shape = regular_shape(answer)
    if response_shape and answer_shape:
        return f"Your response has {describe_shape(response_shape)}, "\
               f"but the expected answer has {describe_shape(answer_shape)}."

    return message
