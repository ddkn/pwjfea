// System setup: Post + Sample + PWJ applied area

SetFactory("OpenCASCADE");

// Geometry: PWJ applied area + sample surface
// PWJ area
Circle(15) = {-7.0, 0, 76.35, 2.5, 0, 2*Pi};
// Sample boundary
Circle(16) = {0, 0, 76.35, 9.5, 0, 2*Pi};

// Ensure Intersections are handled
Coherence;

Extrude {0, 0, -12.7} {
  Curve{3}; Curve{4}; 
}
Curve Loop(3) = {1, 2};
Plane Surface(3) = {3};
Curve Loop(4) = {3, 4};
Curve Loop(5) = {2, 1};
Plane Surface(4) = {4, 5};
Curve Loop(6) = {8, 7};
Plane Surface(5) = {6};
Surface Loop(1) = {3, 4, 1, 2, 5};
Volume(1) = {1};

// Ensure no duplicate surfaces
Recursive Delete {
  Surface{4}; Surface{2}; Surface{1}; 
}

// Post cutout
Cylinder(2) = {0, 0, 69-5.35, 0, 0, 5.35, 6.35, 2*Pi};
Cone(3) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{2}; Delete; }{ Volume{3}; Delete; }
BooleanDifference{ Volume{1}; Delete; }{ Volume{2}; Delete; }

// Post
Cylinder(2) = {0, 0, 0, 0, 0, 69, 6.35, 2*Pi};
Cone(3) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{2}; Delete; }{ Volume{3}; Delete; }

// Set Attributes for MFEM
// NOTE: Sample is made first due to effect of "Coherence"
Physical Volume(1) = {2};
Physical Volume(2) = {1};

Coherence;

Physical Surface(1) = {10};
Physical Surface(2) = {1};
Physical Surface(3) = {2, 3, 4, 5, 9};

Coherence;
