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

- ``bower`` - installs all bower dependencies
- ``update`` - updates all bower dependencies
- ``icons`` - copies the icons (fonts) from the bower directory to the ``static/fonts`` directory.
- ``sass`` - compiles all sass files found in the ``src/`` directory and copies them to ``static/css``
- ``css`` - includes the task ``sass`` **and** will also add the css file ``pygemnts.css`` to the compiled file.
- ``scripts`` - compiles the always needed javascript files (including jquery and bootstrap) into one.
- ``editor-scripts`` - compiles all javascript files needed for the editor to one.
- ``watch`` - watches of any changes happening in ``src/``
- ``default`` - runs all the above tasks in correct order.


You can run a task with gulp like this:

``node_modules/gulp/bin/gulp.js watch``
