# DadaGP v1.1 Encoder/Decoder
DadaGP is:

1. a dataset* of ~26k GuitarPro songs in ~800 genres, converted to a token sequence format for generative language models like GPT2, TransformerXL, etc
2. an encoder/decoder that converts gp3,gp4,gp5 files to/from this token format.

*\* Please contact Dadabots via email or twitter [@dadabots](http://twitter.com/dadabots) to request access to the dataset.*

# Usage

#### ENCODE (guitar pro --> tokens)
`python dadagp.py encode song.gp5 song.txt`

#### DECODE (tokens --> guitar pro)
`python dadagp.py decode song.txt song.gp5`

Note: only gp3, gp4, gp5 files supported by encoder.
Note: rare combinations of instruments and tunings may not be supported.

