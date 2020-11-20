# DadaGP v1.1 Encoder/Decoder
DadaGP is:

1. a dataset* of ~26k GuitarPro songs in ~800 genres, converted to a token sequence format for generative language models like GPT2, TransformerXL, etc
2. an encoder/decoder that converts gp3,gp4,gp5 files to/from this token format.

*\* Please contact Dadabots via email or twitter [@dadabots](http://twitter.com/dadabots) to request access to the dataset for research purposes.*

# Usage

#### ENCODE (guitar pro --> tokens)
```
python dadagp.py encode input.gp3 output.txt [artist_name]
python dadagp.py encode examples/progmetal.gp3 progmetal.tokens.txt unknown
```

#### DECODE (tokens --> guitar pro)
```
python dadagp.py decode input.txt output.gp5
python dadagp.py encode progmetal.tokens.txt progmetal.decoded.gp5
```

Note:
* only gp3, gp4, gp5 files supported by encoder.
* rare combinations of instruments and tunings may not be supported.
* banjo is not supported
* instrument-change events are not supported

