#!/bin/sh

echo request...

curl -o res.xlsx -X POST http://0.0.0.0:8000/public/report/export \
   -F 'file=@./example-data/Joyce_portrait.txt' # или ./example-data/sample.txt

echo file recieved


