import collections
import os

from transformers import AutoTokenizer
from transformers.models.bert.tokenization_bert import BasicTokenizer, BertTokenizer, WordpieceTokenizer, load_vocab, whitespace_tokenize
from transformers.tokenization_utils_base import TextInput


class KorbertTokenizer(BertTokenizer):
    """
    Construct a BERT tokenizer for morpheme-analized data.
    """

    def __init__(
            self,
            vocab_file,
            do_lower_case=True,
            do_basic_tokenize=True,
            never_split=None,
            unk_token="[UNK]",
            sep_token="[SEP]",
            pad_token="[PAD]",
            cls_token="[CLS]",
            mask_token="[MASK]",
            tokenize_chinese_chars=True,
            strip_accents=None,
            **kwargs
    ):
        super(BertTokenizer, self).__init__(
            do_lower_case=do_lower_case,
            do_basic_tokenize=do_basic_tokenize,
            never_split=never_split,
            unk_token=unk_token,
            sep_token=sep_token,
            pad_token=pad_token,
            cls_token=cls_token,
            mask_token=mask_token,
            tokenize_chinese_chars=tokenize_chinese_chars,
            strip_accents=strip_accents,
            **kwargs,
        )
        if not os.path.isfile(vocab_file):
            raise ValueError(
                f"Can't find a vocabulary file at path '{vocab_file}'. To load the vocabulary from a Google pretrained "
                "model use `tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME)`"
            )
        self.vocab = load_vocab(vocab_file)
        self.ids_to_tokens = collections.OrderedDict([(ids, tok) for tok, ids in self.vocab.items()])
        self.do_basic_tokenize = do_basic_tokenize
        if do_basic_tokenize:
            self.space_tokenizer = SpaceTokenizer(
                do_lower_case=do_lower_case,
                never_split=never_split,
                tokenize_chinese_chars=tokenize_chinese_chars,
                strip_accents=strip_accents,
            )
        self.wordpiece_tokenizer = KorbertWordpieceTokenizer(vocab=self.vocab, unk_token=self.unk_token)

    def tokenize(self, morps: TextInput, **kwargs):
        sub_tokens = []
        for token in self.space_tokenizer.tokenize(morps):
            if token not in self.all_special_tokens:
                token += '_'
            for sub_token in self.wordpiece_tokenizer.tokenize(token):
                sub_tokens.append(sub_token)
        return sub_tokens


class SpaceTokenizer(BasicTokenizer):
    """
    Constructs a BasicTokenizer that will run space splitting.
    """

    def __init__(self, do_lower_case=True, never_split=None, tokenize_chinese_chars=True, strip_accents=None):
        super().__init__(
            do_lower_case=do_lower_case,
            never_split=never_split,
            tokenize_chinese_chars=tokenize_chinese_chars,
            strip_accents=strip_accents,
        )

    def tokenize(self, text, never_split=None):
        return super().tokenize(text, never_split=never_split)

    def _run_split_on_punc(self, text, never_split=None):
        if never_split is not None and text in never_split:
            return [text]
        chars = list(text)
        i = 0
        start_new_word = True
        output = []
        while i < len(chars):
            char = chars[i]
            if char == ' ':
                output.append([char])
                start_new_word = True
            else:
                if start_new_word:
                    output.append([])
                start_new_word = False
                output[-1].append(char)
            i += 1
        return ["".join(x) for x in output]


class KorbertWordpieceTokenizer(WordpieceTokenizer):
    """Runs WordPiece tokenization without '##'."""

    def __init__(self, vocab, unk_token, max_input_chars_per_word=100):
        super().__init__(
            vocab=vocab,
            unk_token=unk_token,
            max_input_chars_per_word=max_input_chars_per_word,
        )

    def tokenize(self, text):
        output_tokens = []
        for token in whitespace_tokenize(text):
            chars = list(token)
            if len(chars) > self.max_input_chars_per_word:
                output_tokens.append(self.unk_token)
                continue

            is_bad = False
            start = 0
            sub_tokens = []
            while start < len(chars):
                end = len(chars)
                cur_substr = None
                while start < end:
                    substr = "".join(chars[start:end])
                    if substr in self.vocab:
                        cur_substr = substr
                        break
                    end -= 1
                if cur_substr is None:
                    is_bad = True
                    break
                sub_tokens.append(cur_substr)
                start = end

            if is_bad:
                output_tokens.append(self.unk_token)
            else:
                output_tokens.extend(sub_tokens)
        return output_tokens


if __name__ == "__main__":
    plain = "[CLS] ????????? ???????????? ????????? ???????????????. [SEP] ???????????? ????????????."
    morps = "[CLS] ?????????/NNP ??????/NNG ??????/NNG ??????/NNG ???/JKO ??????/NNG ???/XSV ?????????/EF ./SF [SEP] ??????/NNG ??????/JX ??????/VV ???/EC ???/VX ???/EP ???/EF ./SF"
    print(f"plain={plain}")
    print(f"morps={morps}")

    tokenizer1A = AutoTokenizer.from_pretrained(
        "pretrained/KoELECTRA-Base-v3",
        max_len=512,
        use_fast=True,
    )
    tokenizer1B = BertTokenizer(
        vocab_file="pretrained/KoELECTRA-Base-v3/vocab.txt",
        do_lower_case=False,
        tokenize_chinese_chars=False,
    )
    tokenizer2A = KorbertTokenizer.from_pretrained(
        "pretrained/KorBERT-v1-morp19",
        max_len=512,
        use_fast=False,
        do_lower_case=False,
        tokenize_chinese_chars=False,
    )
    tokenizer2B = KorbertTokenizer(
        vocab_file="pretrained/KorBERT-v1-morp19/vocab.txt",
        do_lower_case=False,
        tokenize_chinese_chars=False,
    )

    print(f"tokens from plain={tokenizer1A.tokenize(plain)}")
    print(f"tokens from plain={tokenizer1B.tokenize(plain)}")
    print(f"tokens from morps={tokenizer2A.tokenize(morps)}")
    print(f"tokens from morps={tokenizer2B.tokenize(morps)}")
