<h1 align = "center">
    Sei Net
</h1>

<div align = "center">
    Construct elements as a net.
</div>

<!-- B-Bone -->
<details>

<summary>BBoneNet</summary>

<div align = "center">
    <img src = "./images/a.webp">
</div>

## Installation

1. Download [sei_bbonenet.py](<./sei_bbonenet.py>).
1. In Blender, go to `Edit -> Preferences -> Add-ons -> Add-ons Settings -> Install from Disk`.
1. Locate and select the downloaded file.
1. Upon successful installation, the tool will apear in the 3D View toolbar (shortcut: **T**).

## Compatibility

This add-on is confirmed to be compatible with the following Blender versions:

- 5.2.0

> [!CAUTION]
> *Issues may arise with other versions.*

## Documentation

- **Radius**  
    Pixel radius for nearest element detection.

- **Snap**  
    Snap to the current armature.

- **Bone**  

    - **Type**  
    Defines whether to create a *Bézier* or *Bendy* bone.

    - **Segments**  
    Number of subdivisions of bone.

    - **Scale**  
    Global scale for the new bones.

    - **Merge Distance**  
    Maximum distance between bones to merge.

    - **Normal**  
    Defines whether to use *Vertex* or *Face* normals for the new bone if available.

> [!TIP]
> *Automatic Weights operator for initial weighting.*  
> *Smooth Corrective modifier for improved deformation.*  
> *Armature constraint for "curve points" (bones).*

</details>

<!-- Nurbs Surface -->
<details>

<summary>SurfaceNet</summary>

<div align = "center">
    <img src = "./images/b.webp">
</div>



## Installation

1. Download [sei_surfacenet.py](<./sei_surfacenet.py>).
1. In Blender, go to `Edit -> Preferences -> Add-ons -> Add-ons Settings -> Install from Disk`.
1. Locate and select the downloaded file.
1. Upon successful installation, the tool will apear in the 3D View toolbar (shortcut: **T**).

## Documentation

> TODO

> [!TIP]
> *[Surface Deform](<../../Group Nodes/geometry nodes/gn_surface_deform.blend>) for deformation.*

</details>

<!-- B-Curves Geometry Nodes -->
<details>

<summary>CurveNet</summary>

<div align = "center">
    <img src = "./images/c.webp">
</div>

## Installation

1. Download [sei_curvenet (wip).py](<./sei_curvenet (wip).py>).
1. In Blender, go to `Edit -> Preferences -> Add-ons -> Add-ons Settings -> Install from Disk`.
1. Locate and select the downloaded file.
1. Upon successful installation, the "Sei" category will appear in the 3D View sidebar (shortcut: **N**).

## Documentation

> TODO

</details>

<!-- Credits -->
## Credits

- [Fernando De Goes](https://fdegoes.github.io/), William Sheffler, Kurt Fleischer [Curvenet](https://research.pixar.com/docs/2022.SiggraphPapers.GSF.pdf)
- Mark Meyer, Haeyoung Lee, Alan Barr, Mathieu Desbrun [Barycentric Coordinates](https://geometry.caltech.edu/pubs/MHBD02.pdf)