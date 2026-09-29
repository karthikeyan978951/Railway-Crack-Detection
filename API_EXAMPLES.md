# API examples

After starting Flask:

## Read sections
GET http://127.0.0.1:5000/api/sections

## Read a section
GET http://127.0.0.1:5000/api/section/TRK-006

## Get weather
GET http://127.0.0.1:5000/api/weather/TRK-006

## Simulate a normal reading
POST http://127.0.0.1:5000/api/simulate/TRK-006
JSON: {"severity":"normal"}

## Simulate a high-risk reading
POST http://127.0.0.1:5000/api/simulate/TRK-006
JSON: {"severity":"high"}

## Simulate a critical reading
POST http://127.0.0.1:5000/api/simulate/TRK-006
JSON: {"severity":"critical"}
