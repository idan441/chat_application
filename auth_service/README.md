# Authentication service
This service is up for all the authentication issues in the CHAT project


## Run service -
```bash
python run.py
```

## Creating the PEM keys
THe service requires two PEM keys to sign and to verify the tokens it creates.
Keys can be in any supported algorithm which is supported by ```pyjwt``` . ( Note that for some of the formats you need to install cryptography ```crypto``` library )

It is recommended to use an asymmetric key algorithm like RS256.

```bash
# https://gist.github.com/ygotthilf/baa58da5c3dd1f69fae9
ssh-keygen -t rsa -P "" -b 4096 -m PEM -f jwtRS256.key
ssh-keygen -e -m PEM -f jwtRS256.key > jwtRS256.key.pub
```

keys should be given in a single line string as ENV VARs. Make sure to put ```\n``` where a newline is in the newly created keys
Using this command will help you - this will replace the newline with ```\n``` . Note that you need to remove the last ```\n``` in the output.
```bash
awk -v ORS='\\n' '1'  jwtRS256.key > private.key
awk -v ORS='\\n' '1'  jwtRS256.key.pub > public.key
``` 

* Example is with keys in RS256 format - make sure to specify it in the ```KEY_ALGORITHM``` NEV VAR!
```bash
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nEXAMPLE_FOR_PRIVATE_KEY\n-----END RSA PRIVATE KEY-----"
JWT_PUBLIC_KEY="-----BEGIN RSA PUBLIC KEY-----\nEXAMPLE_FOR_PUBLIC_KEY\n-----END RSA PUBLIC KEY-----"
KEY_ALGORITHM="RS256"
```


