from core import decrypt
import sys

input = sys.argv[1]
output = sys.argv[2]

image = open(input, "rb").read()

image = decrypt(image)

open(output, "wb").write(image)
