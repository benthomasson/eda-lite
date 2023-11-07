#!/usr/bin/env python3

import sys
from jose import JWTError, jwt
from ifthisthenthat_eda.config import settings
import json


def main(data):

    data = json.loads(data)

    print(settings.secret_key)
    print(settings.algorithm)
    print(data)

    payload = jwt.encode(
        data, settings.secret_key, algorithm=settings.algorithm
    )
    print(payload)

if __name__ == "__main__":
    main(sys.argv[1])


