import contextlib
import json
from urllib.request import urlopen

import urllib3


class MLTagger:
    def __init__(self, netloc: str):
        self.netloc = netloc
        self.api = f"http://{self.netloc}/interface/lm_interface"

    def do_lang(self, text: str):
        param = {"argument": {"analyzer_types": ["MORPH"], "text": text}}
        try:
            with contextlib.closing(urlopen(self.api, json.dumps(param).encode())) as res:
                return json.loads(res.read().decode())['return_object']['json']
        except:
            print("\n" + "=" * 120)
            print(f'[error] Can not connect to WiseAPI[{self.api}]')
            print("=" * 120 + "\n")
            exit(1)

    def tag(self, text: str):
        ndoc = self.do_lang(text)
        morps = ' '.join([f"{m['lemma']}/{m['type']}" for s in ndoc['sentence'] for m in s['morp']])
        return morps


if __name__ == "__main__":
    tagger = MLTagger(netloc="localhost:19001")
    print(tagger.tag(text="운동주는 한국의 독립운동가, 시인, 작가이다."))
