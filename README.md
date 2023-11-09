# PWJFEA

Finite element analysis of experimental apparatus for pulsed water jet force characterization by modelling a post with a cylindrical sample with an applied force in the z-direction that traverses along the cylindrical sample in the x-direction. This work is related my PhD thesis work for understanding the stress-strain of a forced pulsed water jet. The code here is for reference, and hopefully can help others with their work.

## FEM setup

The most user friendly steps to generate meshes in [gmsh](https://gmsh.info/) for use in [MFEM](https://mfem.org/).

## Gmsh

Gmsh is a tool that can be used to generate geometries (*.geo* files) and triangular and quadrilateral meshes. MFEM can only read gmsh v2.2 format, so to ensure the mesh files generated are compatible you need to run,

```
gmsh -format msh22
```

From here you can creat shapes via *Geometry > Elementary Entities > Add*. This generates commands in the .geo file which can be modified later. However, creating more ornate structures is difficult. A better solution is to use CAD software (such as [FreeCAD](https://www.freecad.org/) and export a *Step* file. See the FreeCAD section for more details on more robust CAD design for meshes. **ONLY if you have surfaces**, you cannot modify step files, so while you gain speed in design you loose flexibilty in modifiacions.

One thing to be careful of when building volumes is to have multiple surfaces. You **must** inspect via the visibilty layer if you have duplicate surfaces and use the `Delete` option on *early* created surfaces i.e., low number. Otherwise you will build a mesh that intersects itself and causes issues for FEM modelling. This can be viewed as a crash in `glvis`.

Once you have your `Physical Volumes` defined, you need to apply `Coherence` to tell gmsh that these volumes are truly in conctact. Using `Coherence` will relable the surfaces, so it is best to set `Physical Surfaces` after you apply `Coherence`. 

Gmsh will increment indices of physical objects sequentially. MFEM wants `Physical Surfaces` (MFEM boundary attributes) to be ordered from 1-N, and `Physical Volumes` (MFEM attributes) from 1-N as well. Therefore, you may want to manually label these in the *.geo* scripts.

#### Pulling force boundary overhang

When you want to apply a force from your desired boundary over an area tha isn't fully on the mesh. **You need to be careful**, and use `Coherence` to ensure the boundaries and line intersections are coherent; that is, not to use `Intersection` as this does not yeild the correct result.

Be warned, that elements are drawn from a reference point. How lines intersect, will be drawn from the reference point to the intersections, and numbered from lowest to highest counter clockwise. This will renumber many elements in the mesh as you will have new surfaces not normally seen before. You may need to create multiple meshes depending on your edge case. See the attached figure (fig/coherence.pdf) for more details. If you move 1 dimension(x) over a circular surface, you will need 5 meshes; if you move 2 dimensions (x, y), you may need the original 5 meshes plus 8 more for a total of 13 (unless I counted wrong). That is a lot of work.

Once you have your meshes, you can add some scripting to detect which mesh to use based on the pulling force boundary location; then use regular expressions to update the values. Using the python package `gmsh` will give you the functionality to script generating the mesh output.

### Notes about step files

If you have a *Step* file you can *File > Merge* and import the file, which will include all the element lines, surfaces and volumes! You can then try to add other features to interact with but will be asked to save it as a new *.geo* file. An example of this will be,

```
Merge "myassembly.step";
SetFactory("OpenCASCADE");
Circle(15) = {0, 0, 10, 2.5, 0, 2*Pi};
```

Note that `Circle(15)` is just an example, depending on what shapes you put in after the `Merge`.


From here you can define **physical** *Surfaces* and *Volumes*. Then set up desired mesh parameters and generate a mesh by clicking *Mesh > 1D + 2D + 3D*. The mesh file can be exported for importing into [Glvis](https://glvis.org/) to verify it renders before using MFEM.

## FreeCAD

# Simple part generation

Change *-> Start* to *Part Design*, then generate a *Body* and *Sketch* your base layer. You can extrude, then do all sorts of operations to make a part. Once done click the last operation to select the Part and *Export > Step*.

# More Robust part generation

Utilizing the *Assembly4* module, we can create a Part that can be assembled with other parts to create a more complicated structure. Each part can have their own volumes which means for FEM simulations you can add different material properties. 

1.  In Assembly4: click *Empty Model*. 
2.  Click on the *Model* in the file tree.
3.  Click add a *Body*.
4.  Double click the *Body* to open the *Part Designer* view and create a part as above.
5.  Under Model you can *Create new Datum Object* such as a *New Coordinate System* (LCS). This allows you to anchor other parts to this location.
6.  Choose where and how the LCS will connect to other parts.
7.  You can add as many New Coordinate Systems as you desire.
8.  Repeat 1-6 for as many parts as you need, each with their own file.
9.  To assemble, close and reopen all newly created parts.
10. Repeat steps 1-2.
11. *Import Part into assembly* for each part, choosing where to mate parts via LCS parameters you set in 5.
12. When done, click the *Model* in the assembly and export to a *Step* file

## Running the experiment

```
cd python
python3 experiment.py ../gmsh/system.geo --step-size 0.2 --name "experiment_full_sweep"
```

The data will be output in **paraview/experiment_full_sweep**. You can use Paraview to then view the data as needed, but you will want to fix the `*.pvd` file,

```
python3 fix_pvd.py ../paraview/experiment_full_sweep/experiment_full_sweep.pvd --vtr 21.167 --step-size 0.2
```

Then open `experiment_full_sweep_updated.pvd` in ParaView.

### ParaView

To get a value of the sensor over **time** you need to

* `Apply changes to parameters automatically`
* Click on the pvd in the properties tree
* Go to `Coloring` and change the value to **strain(z,z)**
* Feel free to move and inspect the geometry
* `Probe Location`
* For middle of sensor
  * Set $(x, y, z)$ = (6.35, 0, 30.0)
* Click on `Select Points On`
* Click the row in SpreadSheetView
* Repeat for these, 
  * Set $(x, y, z)$ = (6.35, 0, 31.5)
  * Set $(x, y, z)$ = (6.35, 0, 28.5)
* Select each Probe Location (CTRL-Click)
  * Right click -> Add Filter -> Common -> Group Datasets
* Click `Plot Selection over Time`
* Deselect the features to plot, only select block=1,2,3: strain(z, z)
* You can export to **.tsv** via the SpreadSheetView
  * **DO NOT** export to CSV, columns have commas in them
