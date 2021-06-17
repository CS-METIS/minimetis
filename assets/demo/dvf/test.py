from geojson.geometry import Polygon, Point, Geometry
import typing as t
import json
import dataclasses

point = Point([3, 4])
poly = Polygon([2,4,5,7])
if isinstance(point, Geometry):
    print("Point is geometry")
if isinstance(poly, Geometry):
    print("Polygon is geometry")

print(dataclasses.is_dataclass(Point))

print(Point == Point)
print(Point == Geometry)
print(issubclass(Point, Geometry))
print(Point.__base__)
print(issubclass(Polygon, t.List))

p = Point([5, 6])
print(json.dumps(p))
pp = Polygon([5,7,8,8, 0])
print(json.dumps(pp))

print(" and ".join(["toto", "tutu"]))

p["coordinates"] = [8, 9]
print(json.dumps(p))