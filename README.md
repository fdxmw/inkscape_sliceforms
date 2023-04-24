# inkscape_sliceforms

A collection of [Inkscape](https://inkscape.org/) [extensions](https://inkscape.org/gallery/=extension/) that generate sliceform templates.

![torus models](images/tori.jpg)
![cylinder models](images/cylinders.jpg)
![hyperboloid models](images/hyperboloids.jpg)

This project has template generators for three models: a torus, a cylinder, and a hyperboloid of one sheet. All models are based on the paper [Building a torus with Villarceau sections](http://www.heldermann-verlag.de/jgg/jgg15/j15h1mone.pdf) by María García Monera and Juan Monterde, and [sample templates](https://www.uv.es/monera2/) published by María García Monera.

## Installation

1. Install [Inkscape](https://inkscape.org/).
2. Download this project's [latest release](https://github.com/fdxmw/inkscape_sliceforms/releases/download/r0.2/inkscape_sliceforms-installable-r0.2.zip).
   - If you are browsing GitHub's Releases page, be sure to download the `-installable-` `.zip` file, and not the `Source code` `.zip` file. The `Source code` `.zip` file is not usable by itself, because it does not include the [inkscape_common](https://github.com/fdxmw/inkscape_common) submodule.
3. Unzip the latest release into Inkscape's "User extensions" directory. The location of this directory can be found in Inkscape's Settings dialog box, under `System > User extensions`.
   - If you previously installed an older release (`inkscape_sliceforms-installable-r0.1`), delete the old release's directory from your inkscape extensions directory, otherwise you will have multiple copies of each extension.
4. Restart Inkscape.

If installation succeeded, you should see three new Inkscape menu items:

1. `Extensions > Sliceforms > Cylinder Templates`
1. `Extensions > Sliceforms > Hyperboloid Templates`
1. `Extensions > Sliceforms > Torus Templates`

## Using The Extensions

Select an extension from the `Extensions > Sliceforms` menu. A dialog box should appear, with options to specify the model's dimensions. These dialog boxes have a `Help` tab with recommended settings. The default settings should work well for 110lb (200GSM) cardstock.

Generally, models are easier to assemble when they:

1. Are shorter in height: flatter tori, shorter cylinders and hyperboloids,
1. Have thinner slices: shorter distance from a slice's left side to its right side, and
1. Have larger central holes.

All extensions have these two parameters:

1. Thickness of material
   - The extensions calculate the width of each slot from the material thickness, so it is important to set the material thickness to the actual thickness of your cardstock.
1. Width of material
   - The material width just determines how many templates can be placed in a row, before starting a new row. Note that this is the *usable* material width, which is smaller than the actual material width.
   - For example, with a Cricut cutting machine it is best to avoid cutting within .25 inches of the material's edge, so the usable width of a 8.5" x 11" sheet of cardstock is actually 8" (8.5" - .25" - 25.").

## Making Slices

To make the model, you will need cardstock and a cutting tool.

### Cardstock

I use 110 lb index cardstock (200 GSM), usually "Neenah Index Cardstock" purchased from Amazon. The cardstock must be slightly bent during assembly, so extremely rigid materials like solid wood or metal will not work.

### Cutting Cardstock

If you have access to a cutting machine (Cricut, Silhouette, Glowforge or similar), you can send the templates directly to the cutting machine. I use a Cricut. Cutting machines work best, as the cuts are small and precision is important.

- When loading an Inkscape SVG file in another program, like Cricut Design Space, always double check the dimensions. [Units In Inkscape](https://wiki.inkscape.org/wiki/Units_In_Inkscape) has more background on this debacle.

If you don't have access to a cutting machine, you can print the templates on the cardstock and cut them out manually with scissors or a knife.

- Before printing the templates, remove the fill colors (yellow and blue), unless you want to print the fill colors.
- When cutting manually, it is important to cut *all* sides of each slot. Specifically, you can not make only one cut in the middle of the slot. The slot width accounts for the thickness of the cardstock, and if the slot width is incorrect the slices will not fit together properly.

For a stronger model, align the templates so as many slots as possible are perpendicular to the grain of the cardstock. The extensions assume that the grain runs vertically.

- For example, the grain for Neenah cardstock runs in the longer dimension of the cardstock. The extensions assume the grain is vertical, so orient the cardstock with the longer dimension vertical.

## Assembling Slices

To assemble these models, refer to María García Monera's videos:

* [torus assembly](https://www.youtube.com/watch?v=WVE-HeVFJ1k)
* [cylinder assembly](https://www.youtube.com/watch?v=QfBc0fR64EQ)

The videos are in Spanish, but Youtube's auto-translated captions work well.

There currently is no assembly video for the hyperboloid of one sheet, but the process is very similar to the cylinder.
