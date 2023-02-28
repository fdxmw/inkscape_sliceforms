# inkscape_sliceforms

[Inkscape](https://inkscape.org/) [extensions](https://inkscape.org/gallery/=extension/) that generate sliceform templates.

![torus models](images/tori.jpg) ![cylinder models](images/cylinders.jpg)

This project has template generators for two models: a torus and a cylinder. Both models are based on the paper [Building a torus with Villarceau sections](http://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf) by María García Monera and Juan Monterde, and [sample templates](https://www.uv.es/monera2/) published by María García Monera.

## Installation

1. Install [Inkscape](https://inkscape.org/).
2. Download this project's [latest release](https://github.com/fdxmw/inkscape_sliceforms/releases/download/r0.1/inkscape_sliceforms-installable-r0.1.zip).
   - Make sure you download the `-installable-` `.zip` file, and not the `Source code` `.zip` file. The `Source code` `.zip` file is not usable on its own because it is missing the contents of the [inkscape_common](https://github.com/fdxmw/inkscape_common) submodule.
3. Unzip the release into Inkscape's "User extensions" directory. The location of this directory can be found in Inkscape's Settings dialog box, under `System > User extensions`.
4. Restart Inkscape.

If installation in successful, there should be two new menu items:
1. `Extensions > Sliceforms > Cylinder Template Generator`
2. `Extensions > Sliceforms > Torus Template Generator`

## Usage

Run the extensions to generate templates for a sliceform model with your preferred dimensions. The default settings should work well. Generally, models are easier to assemble when they:
1. Are shorter in height (flatter tori, shorter cylinders),
2. Have thinner slices (shorter distance from a slice's left side to its right side), and
3. Have larger central holes.

Cut the templates. For paper I recommend using 110 lb cardstock (200 gsm). You can print directly on the cardstock and cut out the templates with scissors. If you have access to a cutting machine like a Cricut, Silhouette, or Glowforge, use that to cut directly from the template patterns.

To assemble the model, refer to María García Monera's videos: [torus assembly](https://www.youtube.com/watch?v=WVE-HeVFJ1k), [cylinder assembly](https://www.youtube.com/watch?v=QfBc0fR64EQ).
