# INSTALLATION

Make sure that you have npm (nodejs) installed. You can get it from [
here](https://nodejs.org).

This theme uses SASS (http://sass-lang.com/), a CSS preprocessor, for better development.

Before you can compile the source, you need to get a few dependencies first.
Run (in the directory where **this** README is located):


- ``npm install``

and afterwards

- ``node_modules/gulp/bin/gulp.js``


# TASKS

To get a list of all available tasks you can either read the ``Gulpfile.js``
or see the list below:

    Usage
      gulp [TASK] [OPTIONS...]

    Available tasks
      bower           runs bower
      default         default command [bower, icons, sass, scripts, image]
      editor-scripts  concates all editor related scripts to one file
      help            Display this help text.
      icons           copies the icons to destDir
      image           optimizes the images
      main-scripts    concates all main js files to one js file
      sass            compiles all scss files to one css file
      scripts         [main-scripts, editor-scripts]
      update          updates the bower dependencies
      vendor-scripts  concates all vendor js files to one js file (useful for debugging)
      watch           watches for .scss and .js changes

You can run a task with gulp like this:

``node_modules/gulp/bin/gulp.js watch``


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
6. Edit the ``bower.json`` and ``package.json`` to your needs.
7. Happy theming!

In the end your folder structure should look like this:

    ── example_theme/
        ├── bower_components
        │   └── ...
        ├── node_modules
        │   └── ...
        ├── src
        │   ├── styles.scss
        │   ├── _aurora.scss
        │   ├── _bootstrap-variables.scss
        │   ├── _button.scss
        │   ├── _category.scss
        │   ├── _editor.scss
        │   ├── _fixes.scss
        │   ├── _forum.scss
        │   ├── _management.scss
        │   ├── _misc.scss
        │   ├── _mixins.scss
        │   ├── _navigation.scss
        │   ├── _panel.scss
        │   ├── _profile.scss
        │   ├── _topic.scss
        │   └── _variables.scss
        ├── static
        │   ├── css
        │   ├── fonts
        │   └── js
        ├── templates
        │   └── layout.html
        ├── bower.json
        ├── Gulpfile.js
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
