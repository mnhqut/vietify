need to install

sudo apt install espeak-ng

Choose the conversion rules with `--mode` (defaults to `strong`):

```sh
python main.py --language ipa --mode weak "ˈwɛt"
```

The converter API also accepts a `mode` argument:

```python
ipa_to_vie("ˈwɛt", mode="weak")
```
