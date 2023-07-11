// System setup: Post + Sample + PWJ applied area

SetFactory("OpenCASCADE");

// Geometry: PWJ applied area + sample surface
Circle(16) = {0, 0, 76.35, 9.5, 0, 2*Pi};

Extrude {0, 0, -12.7} {
  Curve{16};
}
Curve Loop(3) = {16};
Plane Surface(3) = {3};
Curve Loop(5) = {18};
Plane Surface(4) = {5};
Surface Loop(1) = {3, 1, 4};
Volume(1) = {1};

// Ensure no duplicate surfaces
Recursive Delete {
  Surface{1};
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

Physical Surface(1) = {8};
Physical Surface(2) = {1};
Physical Surface(3) = {2, 3, 7};

Coherence;