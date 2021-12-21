import gmsh
import trimesh
from stl_to_h5m import stl_to_h5m


def brep_to_h5m(
    brep_filename: str,
    volumes_with_tags: dict,
    h5m_filename: str = 'dagmc.h5m',
    min_mesh_size: int = 30,
    max_mesh_size: int = 50,
    mesh_algorithm: int = 1,
):

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add("made_with_brep_to_h5m")
    volumes = gmsh.model.occ.importShapes(brep_filename)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.Algorithm", mesh_algorithm)
    gmsh.option.setNumber("Mesh.MeshSizeMin", min_mesh_size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", max_mesh_size)
    gmsh.model.mesh.generate(2)
    stl_filenames=[]
    for dim_and_vol in volumes:
        vol_id = dim_and_vol[1]
        entities_in_volume = gmsh.model.getAdjacencies(3,vol_id)
        surfaces_in_volume = entities_in_volume[1]
        ps = gmsh.model.addPhysicalGroup(2, surfaces_in_volume)
        gmsh.model.setPhysicalName(2, ps, f"surfaces_on_volume_{vol_id}")
        gmsh.write(f"volume_{vol_id}.stl")
        stl_filenames.append((vol_id, f"volume_{vol_id}.stl"))
        gmsh.model.removePhysicalGroups([])  # removes all groups
    gmsh.finalize()

    files_with_tags = []
    for filename_vol_id in stl_filenames:
        filename = filename_vol_id[1]
        vol_id = filename_vol_id[0]
        if vol_id in volumes_with_tags.keys():
            mesh = trimesh.load_mesh(filename)
            print('file', filename, 'is watertight', mesh.is_watertight)
            trimesh.repair.fix_normals(mesh)  # reqired as gmsh stl export from brep can get the inside outside mixed up
            new_filename = filename[:-4]+'_with_corrected_face_normals.stl'
            mesh.export(new_filename)
            files_with_tags.append((new_filename, volumes_with_tags[vol_id]))

    stl_to_h5m(
        files_with_tags=files_with_tags,
        h5m_filename=h5m_filename
    )

    return h5m_filename
