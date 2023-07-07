// System setup: Post + Sample + PWJ applied area

SetFactory("OpenCASCADE");

// Geometry: Post
Cylinder(1) = {0, 0, 0, 0, 0, 69, 6.35, 2*Pi};
Cone(2) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{1}; Delete; }{ Volume{2}; Delete; }

// Geometry: PWJ applied area
Circle(6) = {0, 0, 76.35, 2.5, 0, 2*Pi};
// Sample boundary intersection (Required)
Circle(7) = {0, 0, 76.35, 9.0, 0, 2*Pi};
Curve Loop(5) = {6};
Plane Surface(5) = {5};
Curve Loop(6) = {7};
Plane Surface(6) = {6};
// Sample boundary
Circle(8) = {0, 0, 76.35, 9.5, 0, 2*Pi};
BooleanIntersection{ Surface{5}; Delete; }{ Surface{6}; Delete; }

// Geometry: Sample with PWJ applied area
Curve Loop(5) = {8};
Curve Loop(6) = {9};
Plane Surface(6) = {5, 6};
Extrude {0, 0, -12.7} {
  Curve{8};
}
Curve Loop(8) = {11};
Plane Surface(8) = {8};
Surface Loop(4) = {5, 6, 7, 8};
Volume(2) = {4};
Cylinder(3) = {0, 0, 69-5.35, 0, 0, 5.35, 6.35, 2*Pi};
Cone(4) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanDifference{ Volume{2}; Delete; }{ Volume{3}; Delete; }
BooleanDifference{ Volume{2}; Delete; }{ Volume{4}; Delete; }
Recursive Delete {
  Surface{7};
}

// Physical Post and Sample
Physical Volume(1) = {1};
Physical Volume(2) = {2};

// Required to ensure volumes interact
Coherence;

// Physical Surfaces to interact with
Physical Surface(1) = {4};
Physical Surface(2) = {6};
Physical Surface(3) = {2, 9, 8, 7};
