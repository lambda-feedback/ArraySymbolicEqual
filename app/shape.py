import numpy as np


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


def array_shape(array):
    """
    Return the shape of a regular (rectangular) array, e.g. (2, 3) for a
    2x3 matrix, or None if the array is ragged.
    """
    try:
        return np.shape(array)
    except ValueError:
        return None


def entry_lengths(array):
    """
    Return the length of each top-level entry, with -1 for an entry that
    is a single expression rather than a list.
    """
    return np.array([len(e) if isinstance(e, list) else -1 for e in array])


def shape_feedback(response, answer):
    """
    Return feedback explaining how the size of the response differs
    from the answer, or None if they have the same shape.
    """
    if not isinstance(response, list):
        return f"Your response should be an array of {entries(len(answer))}."

    response_shape = array_shape(response)
    answer_shape = array_shape(answer)

    if response_shape is not None and answer_shape is not None:
        if response_shape == answer_shape:
            return None
        return f"Your response has {describe_shape(response_shape)}, "\
               f"but the expected answer has {describe_shape(answer_shape)}."

    # At least one of the arrays is ragged, so numpy can't give its shape
    if len(response) != len(answer):
        return f"Your response has {entries(len(response))}, "\
               f"but the expected answer has {entries(len(answer))}."

    mismatches = np.argwhere(entry_lengths(response) != entry_lengths(answer)).ravel()
    if len(mismatches) == 0:
        # The mismatch is more than one level deep
        return "Your response does not have the same shape as the expected answer."

    i = mismatches[0]
    response_length = int(entry_lengths(response)[i])
    answer_length = int(entry_lengths(answer)[i])
    where = f"Entry ({i + 1})"

    if answer_length == -1:
        return f"{where} should be a single expression, not a list."
    if response_length == -1:
        return f"{where} should be an array of {entries(answer_length)}."
    return f"{where} has {entries(response_length)}, but should have {entries(answer_length)}."
