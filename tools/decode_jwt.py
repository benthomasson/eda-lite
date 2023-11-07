#!/usr/bin/env python3

import sys
from jose import JWTError, jwt
from ifthisthenthat_eda.config import settings


def main(token):

    print(settings.secret_key)
    print(settings.algorithm)
    print(token)

    payload = jwt.decode(
        token, settings.secret_key, algorithms=[settings.algorithm]
    )
    print(payload)

if __name__ == "__main__":
    main(sys.argv[1])


