# INSTALLATION

Make sure that you have npm (nodejs) installed. You can get it from [
here](https://nodejs.org).

This theme uses SASS (https://sass-lang.com/), a CSS preprocessor, for better development.

Before you can compile the source, you need to get a few dependencies first.
This can be achieved by running ``npm install`` in the directory where **this** README is located.


# TASKS

To minimize the dependencies to build and minify our source files, we just use
npm for it.

    Usage
      npm run [TASK]

    Available tasks
      clean
        rm -f node_modules
      autoprefixer
        postcss -u autoprefixer -r static/css/*
      scss
        ./tools/build_css
      uglify
        ./tools/build_js
      imagemin
        imagemin src/img/* -o static/img
      fonts
        ./tools/build_fonts
      build:css
        npm run scss && npm run autoprefixer
      build:js
        npm run uglify
      build:images
        npm run imagemin && npm run fonts
      build:all
        npm run build:css && npm run build:js && npm run build:images
      watch:css
        onchange 'src/scss' -- npm run build:css
      watch:js
        onchange 'src/js' -- npm run build:js
      watch:all
        npm-run-all -p watch:css watch:js

To watch for changes in our JS and SCSS files, you just have to run:

``npm run watch:all``

and upon changes it will automatically rebuild the files.


# CREATING YOUR OWN THEME

If you want to create your own theme based on this theme you have to take care
of a few things first.

1. Create a new folder within the ``themes/`` folder and give it the name
of your theme.
2. Copy the content of the ``aurora/`` folder into your folder theme's folder.
3. Create a new folder called ``static/`` in your themes folder.
4. (Optional) If you plan on modifying templates you also need to create a
``templates/`` folder where your templates are located. To edit a template,
you have to copy them over from flaskbb's template folder into your template
folder
5. Add some information about your theme using the ``info.json``. Have look at
aurora's ``info.json`` for an example.
6. Edit the ``package.json`` to your needs.
7. Happy theming!

In the end your folder structure should look like this:

    ── example_theme/
        ├── node_modules
        │   └── ...
        ├── src
        │   ├── img
        │   │   └── ...
        │   ├── js
        │   │   └── ...
        │   └── scss
        │       └── ...
        ├── static
        │   ├── img
        │   ├── css
        │   ├── fonts
        │   └── js
        ├── templates
        │   ├── ...
        │   └── layout.html
        ├── tools
        │   ├── build_css
        │   ├── build_fonts
        │   └── build_js
        ├── info.json
        ├── LICENSE
        ├── package.json
        └── README.md


## info.json

This file should contain following information about a theme:

* ``"application": "flaskbb"`` - The name of the application, in our case this should always be flaskbb
* ``"identifier": "aurora"`` - The unique name of the theme. This identifier should match the themes folder name!
* ``"name": "Aurora"`` - Human readable name of the theme
* ``"author": "sh4nks"`` - The name of the author.
* ``"license": "BSD 3-Clause"`` - Every theme should include define a license under which terms the theme can be used.
* ``"description": "The default theme for FlaskBB."`` - A short description about the theme. For example: "A minimalistic blue theme".
* ``"version": "1.0.0"`` - The version of the theme.
