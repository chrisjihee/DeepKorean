import argparse
import contextlib
import json
import shutil
from pathlib import Path
from urllib.request import urlopen

from datasets import load_dataset

from base.io import make_parent_dir


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


def convert_json_lines(infile, outfile):
    infile = Path(infile)
    outfile = Path(outfile)
    print()
    print('=' * 120)
    print(f"* Infile: {infile}")
    print(f"* Outfile: {outfile}")
    example_count = 0
    example_data = []
    with infile.open('r') as inp:
        for line in inp.readlines():
            example_data.append(json.loads(line))
            example_count += 1
    print(f"  - #example={example_count}")

    outfile.parent.mkdir(parents=True, exist_ok=True)
    with outfile.open('w') as out:
        json.dump({"version": f"datasets_1.0", "data": example_data}, out, ensure_ascii=False, indent=4)
    print('=' * 120)


def download_task_data(data_dir, data_name, task_name):
    data_dir = Path(data_dir)
    tmpdir = data_dir / f"{data_name}-{task_name}-temp"
    outdir = data_dir / f"{data_name}-{task_name}"
    # load_dataset(data_name)  # for all_task_names
    raw_datasets = load_dataset(data_name, task_name)
    raw_datasets.save_to_disk(str(tmpdir))
    for k, dataset in raw_datasets.items():
        dataset.to_json(tmpdir / f"{k}.json", force_ascii=False)
        convert_json_lines(tmpdir / f"{k}.json", outdir / f"{k}.json")
    info_file = tmpdir / "train" / "dataset_info.json"
    if info_file.exists() and info_file.is_file():
        shutil.copyfile(info_file, outdir / "info.json")
    if tmpdir.exists() and tmpdir.is_dir():
        shutil.rmtree(tmpdir)


def download_task_dataset(data_dir, data_name, task_names):
    for task_name in task_names:
        download_task_data(data_dir, data_name, task_name)


def tag_kor_sentence(infile, outfile):
    tagger = MLTagger(netloc="129.254.164.137:19001")
    infile = Path(infile)
    outfile = make_parent_dir(outfile)
    print()
    print('=' * 120)
    print(f"* Infile: {infile}")
    print(f"* Outfile: {outfile}")
    print('-' * 120)
    with infile.open() as inp:
        contents = json.load(inp)
    ll = len(contents['data'])
    for i in range(len(contents['data'])):
        print(f"- [{i + 1}/{ll}] {contents['data'][i]['guid']}")
        contents['data'][i]['sentence1_morp'] = tagger.tag(contents['data'][i]['sentence1'])
        contents['data'][i]['sentence2_morp'] = tagger.tag(contents['data'][i]['sentence2'])
    with outfile.open("w") as out:
        json.dump({"version": f"datasets_1.0", "data": contents['data']}, out, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--glue", default="", type=str, required=False,
                        help=f"What tasks of GLUE to make: cola, sst2, mrpc, qqp, stsb, mnli, mnli_mismatched, mnli_matched, qnli, rte, wnli, ax")
    parser.add_argument("--klue", default="", type=str, required=False,
                        help=f"What tasks of KLUE to make: ynat, sts, nli, ner, re, dp, mrc, wos")
    parser.add_argument("--tag", default=0, type=int, required=False,
                        help=f"Tag Korean sentence pairs for KLUE-STS")
    args = parser.parse_args()

    if args.glue != "":
        download_task_dataset("data", "glue", [x.strip() for x in args.glue.split(',')])

    if args.klue != "":
        download_task_dataset("data", "klue", [x.strip() for x in args.klue.split(',')])

    if args.tag > 0:
        tag_kor_sentence("data/klue-sts/train.json", "data/klue-sts-morp/train.json")
        tag_kor_sentence("data/klue-sts/validation.json", "data/klue-sts-morp/validation.json")
