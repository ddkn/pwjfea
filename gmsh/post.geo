//+
SetFactory("OpenCASCADE");
Cylinder(1) = {0, 0, 0, 0, 0, 69, 6.35, 2*Pi};
//+
Cone(2) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
//+
BooleanUnion{ Volume{1}; Delete; }{ Volume{2}; Delete; }
//+
Physical Volume(1) = {1};
//+
Physical Surface(3) = {3};
//+
Physical Surface(4) = {1, 2, 4};
