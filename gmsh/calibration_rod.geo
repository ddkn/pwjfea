//+
SetFactory("OpenCASCADE");
Cylinder(1) = {0, 0, 0, 0, 0, 0.05, 0.005, 2*Pi};
//+
Coherence;
//+
Physical Volume(1) = {1};
//+
Physical Surface(1) = {3};
//+
Physical Surface(2) = {2};
//+
Physical Surface(3) = {1};
