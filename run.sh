#!/bin/bash
wget http://pgoapi.com/pgoencrypt.tar.gz
tar -xf pgoencrypt.tar.gz
cd pgoencrypt/src/
make
mv libencrypt.so ../../encrypt.so
cd ../../
python app.py