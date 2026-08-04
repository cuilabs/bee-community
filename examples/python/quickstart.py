import os

from bee_sdk import Bee

bee = Bee(api_key=os.environ["BEE_API_KEY"])
result = bee.chat("What is Bee?", model="bee-cell")

print(result)
