import re

import torch
from sqlalchemy.util import OrderedSet


def horizontal_line(c="=", w=256, t=0, b=0):
    return "\n" * t + c * w + "\n" * b


morpheme_pattern = re.compile("([^ ]+?/[A-Z]{2,3})[+]?")


def to_morphemes(text: str, pattern=morpheme_pattern):
    return ' '.join(x.group(1) for x in pattern.finditer(text))


def append_intersection(a, b):
    return list(OrderedSet(a).difference(b)) + list(OrderedSet(a).intersection(b))


def to_tensor_batch(batch, input_keys):
    for key in input_keys:
        if isinstance(batch[key], list) and isinstance(batch[key][0], torch.Tensor):
            batch[key] = torch.stack(batch[key], dim=1)
    return batch
