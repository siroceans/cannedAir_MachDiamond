import shutil
import os

def maresMesher():
    """
    Parameters
    ----------
    x : int
        x distance of mesh. in mm
    y : int
        y distance of mesh (excluding inlet height of 1 mm), only in one direction. in mm
    xcells : int
        number of cells in x .
    ycells : in 
        number of cells in y (for each block).

    Returns
    -------
    None.

    """
    
    # Defining the header file and blockMeshDict file name.
    source_file = "openfoamheader"
    destination_file = "system/blockMeshDict"
       
    # User input!
    x = int(input("\nInput the x distance for the mesh [mm]: "))
    y = int(input('\nInput the y distance for the mesh (only up without counting the inlet height) [mm]: '))
    xcells = int(input("\nInput the number of cells for each block in x direction: "))
    ycells = int(input("\nInput the number of cells for each block in y direction: "))

    mdx = x/xcells
    mdy = y/ycells
    if mdx > mdy:
        dx = mdy * 10 ** (-3) 
        print("the mimimum Δx is {:.4f} mm".format(mdy))
    else:
        print("The minimum Δx is {:.4f} mm".format(mdx))
        dx = mdx * 10 ** (-3)

    mach = 3    # Assumed maximum mach number throughout the flow? Modify it depending on how the simulation behaves!
    gamma = 1.4 # For air, change if it is difluorethane.
    T = 295     # Room temperature in Kelvin (to estimate for courant condition only!)
    R = 287     # Ideal gas constant for air in J/kgK for air
    maxco = 0.4 # Again, change depending on stability. 
    dt = (maxco * dx) / (mach * (gamma * R * T)**0.5)

    print("The required Δt to satisfy the courant condition given the mesh is {:.8f} s".format(dt))
    
    
    ## Initial block
    vertices_0 = [[0, 0, 0], 
                  [0, 0, 1], 
                  [x, 0, 1], 
                  [x, 0, 0], 
                  [0, 1, 0], 
                  [0, 1, 1], 
                  [x, 1, 1], 
                  [x, 1, 0]]
    
    ## Vertices going up 
    verticesup = []
    
    for i in range(2*y):
        verticesup.append([0, i+2, 0])
        verticesup.append([0, i+2, 1])
        verticesup.append([x, i+2, 1])
        verticesup.append([x, i+2, 0])
       
    allvertex = vertices_0 + verticesup  # Adding the initial vertices to the list
    
    ## Shifting all vertices down so that inlet[0] is at origin
    for i in range(len(allvertex)):
        allvertex[i][1] -= y
           
    ## Creating top blocks: 
    blocks = []; 
    nblocks = 1 + 2*y # Total number of blocks!
    counter = 0
    cstart = 0 # Current block start!
    while counter < nblocks:
        counter += 1
        cblock = []
        for i in range(8):
            cblock.append(cstart+i)
        cstart += 4
        blocks.append(cblock)
           
    ## Checking for in and out - empty faces in z 
    totalb = len(blocks)
    
    infaces = []
    for i in range(totalb):
        infaces.append([blocks[i][1], blocks[i][2], blocks[i][6], blocks[i][5]])
        
    outfaces = []
    for i in range(totalb):
        outfaces.append([blocks[i][0], blocks[i][3], blocks[i][7], blocks[i][4]])
    
    ## Checking for freestream inlet patch faces
    freestreamInletFaces = []
    for i in range(totalb):
        if i != y:
            freestreamInletFaces.append(([blocks[i][0], 
                                          blocks[i][1], 
                                          blocks[i][5], 
                                          blocks[i][4]]))

    ## Checking for outlet patch faces
    opatchfaces = []
    for i in range(totalb):
        opatchfaces.append(([blocks[i][2], 
                                blocks[i][3],
                                blocks[i][7],
                                blocks[i][6]]))

    ## Checking for freestream patch faces and Inlet patch face. 
    freestreamfaces = []
    for i in range(totalb):
        if i == 0:
            freestreamfaces.append(([blocks[i][0], 
                                     blocks[i][1], 
                                    blocks[i][2], 
                                    blocks[i][3]]))
        elif i == (totalb-1):
            freestreamfaces.append(([blocks[i][4], 
                                     blocks[i][5], 
                                     blocks[i][6], 
                                     blocks[i][7]]))
        elif i == y: 
            inletface = ([blocks[i][0],
                          blocks[i][1],
                          blocks[i][5],
                          blocks[i][4]])
   
    ## CREATINGFILE
    # Writing the header to blockMeshDict. 
    if os.path.exists(source_file):
        # Copy the file. This will copy the file's content and permissions.
        shutil.copy(source_file, destination_file)
 
    with open(destination_file, 'a') as file:
        stuff1 =("""FoamFile
{
version     2.0;
format      ascii;
class       dictionary;
object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

scale   0.001;

vertices
(\n""")
        file.write(stuff1)
        
        for number in range(len(allvertex)):
            line = f"    ({allvertex[number][0]} {allvertex[number][1]} {allvertex[number][2]})\n"
            file.write(line)
        file.write(");\n\n")
        
        stuff2 =("""blocks
(\n""")

        file.write(stuff2)
        
        for number in range(len(blocks)):
            line = f"   hex ({blocks[number][0]} {blocks[number][1]} {blocks[number][2]} {blocks[number][3]} {blocks[number][4]} {blocks[number][5]} {blocks[number][6]} {blocks[number][7]}) ({xcells} {ycells} 1) simpleGrading (1 1 1)\n"
            file.write(line)
            
        stuff3 = (""");
                   
edges
(
);

boundary 
(
inlet
{
    type patch;
    faces
    (\n""")
         
        file.write(stuff3)
        file.write(f"           ({inletface[0]} {inletface[1]} {inletface[2]} {inletface[3]})")
        stuff32 = ("""
    );
}
 
outlet
{
    type patch;
    faces
    (\n""")
                  
        file.write(stuff32)
        
        for i in range(len(opatchfaces)):
            line = f"           ({opatchfaces[i][0]} {opatchfaces[i][1]} {opatchfaces[i][2]} {opatchfaces[i][3]})\n"
            file.write(line)
                
        stuff33 = ("""
    );
}
 
freestreamInlet
{
    type patch;
    faces
    (\n""")
                  
        file.write(stuff33)
        
        for i in range(len(freestreamInletFaces)):
            line = f"           ({freestreamInletFaces[i][0]} {freestreamInletFaces[i][1]} {freestreamInletFaces[i][2]} {freestreamInletFaces[i][3]})\n"
            file.write(line)
            
        stuff34 = ("""
    );
}
 
freestream
{
    type patch;
    faces
    (\n""")
                  
        file.write(stuff34)
        
        for i in range(len(freestreamfaces)):
            line = f"           ({freestreamfaces[i][0]} {freestreamfaces[i][1]} {freestreamfaces[i][2]} {freestreamfaces[i][3]})\n"
            file.write(line)
 
        stuff4 = ("""        
    );
    }
   
frontback
{
type empty;
faces
    (\n""")
      
        file.write(stuff4)
        for i in range(len(infaces)):
            line = f"           ({infaces[i][0]} {infaces[i][1]} {infaces[i][2]} {infaces[i][3]})\n"
            file.write(line)
        file.write("// outfaces\n")
        for i in range(len(outfaces)):
            line = f"           ({outfaces[i][0]} {outfaces[i][1]} {outfaces[i][2]} {outfaces[i][3]})\n"
            file.write(line)
        stuff5 = ("""        
    );
}

);

mergePatchPairs
(
);


// ************************************************************************* //""")
        file.write(stuff5)


maresMesher()