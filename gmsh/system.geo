//+
SetFactory("OpenCASCADE");
//+
// Geometry: Post
//+
Cylinder(1) = {0, 0, 0, 0, 0, 69, 6.35, 2*Pi};
//+
Cone(2) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
//+
BooleanUnion{ Volume{1}; Delete; }{ Volume{2}; Delete; }
//+
// Geometry: Sample
//+
Circle(6) = {0, 0, 76.35, 2.5, 0, 2*Pi};
//+
Circle(7) = {0, 0, 76.35, 9.5, 0, 2*Pi};
//+
Curve Loop(5) = {6};
//+
Plane Surface(5) = {5};
//+
Curve Loop(6) = {6};
//+
Curve Loop(7) = {7};
//+
Plane Surface(6) = {6, 7};
//+
Extrude {0, 0, -12.7} {
  Curve{7};
}
//+
Curve Loop(9) = {9};
//+
Plane Surface(8) = {9};
//+
Surface Loop(2) = {5, 6, 7, 8};
//+
Volume(2) = {2};
//+
Cylinder(3) = {0, 0, 69-5.35, 0, 0, 5.35, 6.35, 2*Pi};
//+
Cone(4) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
//+
BooleanDifference{ Volume{2}; Delete; }{ Volume{3}; Delete; }
//+
BooleanDifference{ Volume{2}; Delete; }{ Volume{4}; Delete; }
//+
Recursive Delete {
  Surface{6}; 
}
//+
Recursive Delete {
  Surface{7}; 
}
//+
Physical Volume(1) = {1};
//+
Physical Volume(2) = {2};
//+
Coherence;
//+
Physical Surface(1) = {4};
//+
Physical Surface(2) = {6};
//+
Physical Surface(3) = {2, 9, 8, 7};
