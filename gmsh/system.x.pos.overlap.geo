// System setup: Post + Sample + PWJ applied area

SetFactory("OpenCASCADE");

// Geometry: PWJ applied area + sample surface
// PWJ area
Circle(15) = {9.5, 0, 76.35, 2.5, 0, 2*Pi};
// Sample boundary
Circle(16) = {0, 0, 76.35, 9.5, 0, 2*Pi};

// Ensure Intersections are handled
Coherence;
Recursive Delete {
  Curve{1}; Curve{3}; 
}

// Ensure no duplicate surfaces
Extrude {0, 0, -12.7} {
  Curve{5}; Curve{6}; Curve{4}; 
}
Curve Loop(4) = {4, 2, 6};
Plane Surface(4) = {4};
Curve Loop(5) = {5, -2};
Plane Surface(5) = {5};
Curve Loop(6) = {9, 11, 12};
Plane Surface(6) = {6};
Surface Loop(1) = {4, 3, 2, 1, 6, 5};
Volume(1) = {1};
Recursive Delete {
  Surface{2}; Surface{3}; Surface{1}; 
}

// Post cutout
Cylinder(2) = {0, 0, 69-5.35, 0, 0, 5.35, 6.35, 2*Pi};
Cone(3) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{2}; Delete; }{ Volume{3}; Delete; }
BooleanDifference{ Volume{1}; Delete; }{ Volume{2}; Delete; }

// Post
// NOTE: Sample is made first due to effect of "Coherence"
Cylinder(2) = {0, 0, 0, 0, 0, 69, 6.35, 2*Pi};
Cone(3) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{2}; Delete; }{ Volume{3}; Delete; }

// Set Attributes for MFEM
// NOTE: Sample is made first due to effect of "Coherence"
Physical Volume(1) = {2};
Physical Volume(2) = {1};

Coherence;

Physical Surface(1) = {11};
Physical Surface(2) = {1};
Physical Surface(3) = {3, 4, 2, 6, 5, 10};

Coherence;
