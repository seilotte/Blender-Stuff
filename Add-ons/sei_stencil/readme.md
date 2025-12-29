<h1 align = "center">Sei Stencil</h1>

<p align = "center">This add-on creates a stencil pass as a Blender image.</p>

<div align="center">
    <img src="./images/a.webp">
</div>

## Installation

1. Download [sei_stencil.py](./sei_stencil.py).
1. In Blender, go to `Edit -> Preferences -> Add-ons -> Add-ons Settings -> Install from Disk`.
1. Locate and select the downloaded file.
1. Upon successful installation, the "Sei" category will appear in the 3D View sidebar (shortcut: **N**).

## Compatibility

This add-on is confirmed to be compatible with the following Blender versions:

- 4.4.0
- 5.0.0

> [!CAUTION]
> *Issues may arise with other versions.*

## Documentation

- **Collection**  
    Specifies the collection used to retrieve objects for the stencil.

- **Visualizer**  
    Writes the stencil to an image named "_SSTENCIL".  
    Supported object types: *MESH*  
    Supported attributes: *VERTEX COLOURS*

- **Render Animation**  
    Applies the stencil during rendering.  
    Supports a single-frame render.

> [!IMPORTANT]
> *Ensure the **image** interpolation and coordinates are correctly configured. For the shader editor, use "Closest" and "Window Coordinates".*

- **Resolution X**  
    Defines the resolution of the scene and stencil along the x-axis.

- **Resolution Y**  
    Defines the resolution of the scene and stencil along the y-axis.

- **Resolution %**  
    Defines the resolution percentage for the scene and stencil.

> [!TIP]
> *Be sure to set the correct values before rendering.*