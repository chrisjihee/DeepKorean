import json

import urllib3


def tag_morps(text: str):
    openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU"
    accessKey = "ecc18e45-d0a9-42a5-ab32-c61d2909795b"

    analysisCode = "morp"
    requestJson = {
        "access_key": accessKey,
        "argument": {
            "text": text,
            "analysis_code": analysisCode
        }
    }

    http = urllib3.PoolManager()
    response = http.request("POST", openApiURL, headers={"Content-TYpe": "application/json; charset=UTF-8"}, body=json.dumps(requestJson))

    print(f"responseCode = {response.status}")
    obj = json.loads(str(response.data, "utf-8"))
    ndoc = obj["return_object"]
    for sentence in ndoc['sentence']:
        morps = []
        for morp in sentence['morp']:
            morps.append(f"{morp['lemma']}/{morp['type']}")
        print(" ".join(morps))


if __name__ == "__main__":
    tag_morps(text="운동주는 한국의 독립운동가, 시인, 작가이다.")
