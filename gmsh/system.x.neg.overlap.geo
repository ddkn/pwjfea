// System setup: Post + Sample + PWJ applied area

SetFactory("OpenCASCADE");

// Geometry: PWJ applied area + sample surface
// PWJ area
Circle(15) = {-9.5, 0, 66.35, 2.5, 0, 2*Pi};
// Sample boundary
Circle(16) = {0, 0, 66.35, 9.5, 0, 2*Pi};

// Ensure Intersections are handled
Coherence;
Recursive Delete {
  Curve{2}; 
}
Extrude {0, 0, -12.7} {
  Curve{4}; Curve{5}; Curve{6}; 
}
Curve Loop(4) = {1, 5, 3};
Plane Surface(4) = {4};
Curve Loop(5) = {4, -1, -3, 6};
Plane Surface(5) = {5};
Curve Loop(6) = {12, 9, 11};
Plane Surface(6) = {6};
Surface Loop(1) = {6, 3, 2, 1, 5, 4};
Volume(1) = {1};

// Ensure no duplicate surfaces
Recursive Delete {
  Surface{3}; Surface{2}; Surface{1}; 
}

// Post cutout
Cylinder(2) = {0, 0, 59-5.35, 0, 0, 5.35, 6.35, 2*Pi};
Cone(3) = {0, 0, 59, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{2}; Delete; }{ Volume{3}; Delete; }
BooleanDifference{ Volume{1}; Delete; }{ Volume{2}; Delete; }

// Post
Cylinder(2) = {0, 0, 0, 0, 0, 59, 6.35, 2*Pi};
Cone(3) = {0, 0, 59, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{2}; Delete; }{ Volume{3}; Delete; }

// Set Attributes for MFEM
// NOTE: Sample is made first due to effect of "Coherence"
Physical Volume(1) = {2};
Physical Volume(2) = {1};

Coherence;

Physical Surface(1) = {11};
Physical Surface(2) = {7};
Physical Surface(3) = {6, 4, 3, 2, 1, 10};

Coherence;
