// System setup: Post + Sample + PWJ applied area

SetFactory("OpenCASCADE");

// Geometry: Post
Cylinder(1) = {0, 0, 0, 0, 0, 69, 6.35, 2*Pi};
Cone(2) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{1}; Delete; }{ Volume{2}; Delete; }

// Geometry: Sample with PWJ applied area
Cylinder(2) = {0, 0, 69-5.35, 0, 0, 5.35, 6.35, 2*Pi};
Cone(3) = {0, 0, 69, 0, 0, 1, 6.35, 5.35, 2*Pi};
BooleanUnion{ Volume{3}; Delete; }{ Volume{2}; Delete; }
Circle(12) = {0, 0, 76.35, 9.5, 0, 2*Pi};
Extrude {0, 0, -12.7} {
  Curve{12};
}
Curve Loop(12) = {14};
Plane Surface(12) = {12};

// Geometry: PWJ applied area + sample surface
// PWJ area
Circle(15) = {0, 0, 76.35, 2.5, 0, 2*Pi};
// Intersection boundary
Circle(16) = {0, 0, 76.35, 9.45, 0, 2*Pi};
Curve Loop(13) = {15};
Plane Surface(13) = {13};
Curve Loop(14) = {16};
Plane Surface(14) = {14};
BooleanIntersection{ Surface{13}; Delete; }{ Surface{14}; Delete; }
Curve Loop(13) = {12};
// NOTE: Depending on pwj intersection with boundary we get different
// 	 amount of curves and varies between 1 - 3, with id: 15, 16, 17
//	 There is only 3 curves if the intersection has a larger area.
//
//       If error on 'Plane Surface(14)' try these combinations,
//       Curve Loop(14) = {15};
//	 Curve Loop(14) = {16, 15};
//	 Curve Loop(14) = {15, 17, 16};
Curve Loop(14) = {15};
Plane Surface(14) = {13, 14};
Surface Loop(3) = {13, 14, 9, 12};

// Sample volume final
Volume(3) = {3};
Recursive Delete {
  Surface{9};
}
BooleanDifference{ Volume{3}; Delete; }{ Volume{2}; Delete; }

// Physical Post and Sample
Physical Volume(1) = {1};
Physical Volume(2) = {3};

// Required for volumes in contact
Coherence;

Physical Surface(1) = {4};
Physical Surface(2) = {6};
Physical Surface(3) = {2, 9, 8, 7};
